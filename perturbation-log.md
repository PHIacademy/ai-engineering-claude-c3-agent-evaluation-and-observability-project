# Perturbation Log

For each system, make one deliberate change to an input or configuration, predict the outcome, run it, and record what actually happened. See the starters in the Instructions, or design your own (your own experiment earns more credit).

---

### System 1 — validated, routed pipeline

- **Change I made (file + what I changed):**
  Wrote perturb_us01.py — a standalone script that builds a synthetic extractor response with `exclusions` (a required field) set to `None`, simulating a source policy document that never states its exclusion clauses. Only one response is queued in RecordedClient, so any retry attempt beyond the first call would raise an AssertionError.

- **Command I ran:**
  `.venv/bin/python perturb_us01.py | tee 01-pipeline-perturbation.txt`

- **What I predicted:**
  validator.py classifies a null required field as `missing_source`, and retry.py returns immediately on that category. I expected a RetryFutileEscalation on `exclusions` after exactly one API call, with no AssertionError from the exhausted RecordedClient.

- **What actually happened (paste the key output line):**
  ```
  result type: RetryFutileEscalation
  field: exclusions
  detected_pattern: exclusions_absent
  category: missing_source
  API calls made: 1
  ```
- **How this differs from the unperturbed run:**
  A well-formed response (all fields populated) returns a PolicyExtraction on the first call with no escalation. A format/consistency failure (e.g. negative premium) retries — 2 calls — because it's recoverable by re-prompting. This missing-source case escalates immediately with zero retries spent, confirming the pipeline treats "data isn't in the source" as fundamentally different from "the model got the format wrong."

---

### System 2 — schema-enforced two-pass extraction

- **Change I made (file + what I changed):**
  Wrote perturb_us02.py, reusing the real line items from discrepancy-run.txt (base=5416.67, bonus=1250.0, commission=2140.0, overtime=385.5, other=450.0 -> calculated=9642.17). Rather than the  document's actual $1250 discrepancy, I edited stated_monthly_total to sit only $1.50 above the true calculated sum, to test the exact tolerance boundary rather than a large obvious error.

- **Command I ran:**
 `.venv/bin/python perturb_us02.py | tee perturbation.txt `

- **What I predicted:**
With stated_monthly_total set exactly equal to the calculated total, validate() should report consistent=True. Nudging it by +$1.50 should flip it to consistent=False with exactly one discrepancy, since the default tolerance is $1.00 (confirmed by test_ac_04_02_default_tolerance_is_one_dollar).

- **What actually happened (paste the key output line):**
  ```
  calculated_total (from real fixture line items): 9642.17

  --- Exact match (stated == calculated) ---
  consistent: True, discrepancies: []

  --- Perturbed: stated_monthly_total edited to 9643.67 (+$1.50) ---
  consistent: False
    field=total_monthly_income calculated=9642.17 stated=9643.67 delta=-1.5
  ```
- **How this differs from the unperturbed run:**
discrepancy-run.txt (the real income_sum_mismatch.txt replay) shows the validator catching a $1250 error — an obviously wrong total. This perturbation shows the safeguard isn't just catching gross mistakes: even a $1.50 drift on the exact same underlying real-world numbers trips the check, while $1.00 or less would pass. The validator enforces a precise arithmetic boundary, not a fuzzy "looks about right" check.

---

### System 3 — multi-source synthesis

- **Change I made (file + what I changed):**
No file edit — passed the `--simulate-timeout` configuration flag to force the `logistics` reader to fail partway through, per the starter. Compared investigate-run.txt (no flag) against timeout-run.txt (flag set).

- **Command I ran:**
`.venv/bin/supply-chain-investigate meridian --offline | tee investigate-run.txt`
`.venv/bin/supply-chain-investigate meridian --offline --simulate-timeout  | tee timeout-run.txt`

- **What I predicted:**
Based on test_coordinator.py (test_coordinator_proceeds_and_annotates_gap, test_logistics_timeout_returns_partial_and_context), I expected the run to complete rather than abort, with logistics' exclusive metric moved to Incomplete and annotated with a timeout failure context, and the header to explicitly name logistics as unavailable.

- **What actually happened (paste the key output line):**
From `timeout-run.txt`:
  ```
   Sources unavailable: logistics unavailable (timeout)
  ```
  ```
    ### late_shipment_count  _[missing source: timeout reading logistics]_
     - missing source: timeout reading logistics
  ```
    Unexpected secondary effect, confirmed by comparing `timeout-run.txt` against `investigate-run.txt`:
      - investigate-run.txt shows on_time_delivery_rate as **Contested** ⚠️ ESCALATE, with both values listed: (~95% vs ~78%) 
      - and the Contested section in timeout-run.txt is left with no entries: _none_
    

- **How this differs from the unperturbed run:**
The healthy run (investigate-run.txt) surfaces the on-time-delivery conflict as a high-priority escalation precisely because two sources disagree (95.0 vs 78.0), and late_shipment_count is a normal Well-Established single-source metric. Losing logistics doesn't just create a new Incomplete entry (late_shipment_count) as expected — it also removes a real, high-impact conflict from visibility, since the disagreeing source is gone. This shows a coverage gap can silently mask risk (a contested metric quietly becomes uncontested) rather than only ever adding visible gaps — worth flagging as a monitoring blind spot in the reflection.
