# Reflection Brief — Evaluation and Observability Capstone

**Name:** Lo Kai Cheung, Stanley
**Date:** 2026-08-24

> Ground every answer in your own run. When a question asks for a number, file name, or line, paste
> it from your artifacts — a reviewer should be able to find it. Answers that are correct in the
> abstract but cite nothing do not meet the bar. Keep it short and specific.

---

## 0. Environment

| Field | Value |
|---|---|
| OS & version | Linux 6.6.97+ x86_64 GNU/Linux |
| Python version | Python 3.13.0 |
| Date run | 2026-08-24 to 2026-08-25 |
| Ran any system live? (which) | No — all extraction runs used `--mode replay` (normalized-integer.txt, extract-run.txt, discrepancy-run.txt); live tests show as SKIPPED in tests.txt|

---

## 1. Validated, routed pipeline

| Evidence | Value |
|---|---|
| Passing test count | 45 passed, 3 skipped — 01-policy-pipeline/tests.txt |
| Static analysis | mypy: "Success: no issues found in 11 source files" (01-policy-pipeline/static-checks-mypy.txt); ruff: "All checks passed!" (01-policy-pipeline/static-checks-ruff.txt) |
| Routing output file | routing_decisions.json (generated via generate_routing_output.py — no API access needed; route_extraction() and write_routing_decisions() are pure Python, no model calls involved). **Scope note:** generated from three hand-constructed extraction records, not the bundled document set — route_extraction()/write_routing_decisions() require no API access, but running the pipeline over the actual bundled documents would require a live extraction pass this environment couldn't perform.|
| auto_approve / human_review / spot_check counts | 0 / 2 / 1 — routing-output.txt |



**1a. Retry boundary.**
> From perturb_us01.py's output (perturbation-log.md, System 1):
> `result type: RetryFutileEscalation`, `field: exclusions`, `detected_pattern: exclusions_absent`, `category: missing_source`, `API calls made: 1`.
> The system made exactly one API call. Retrying a missing_source failure is futile because no amount of re-prompting supplies information the source document never contained — the model can only guess or fabricate a value, which is worse than escalating: escalation costs zero extra API spend and routes to a human who can go find the missing data, while a blind retry burns budget and risks a confidently wrong answer that looks legitimate.

**1b. Reading the router.**
> From routing_decisions.json, record POL-2025-103 (policy_type: umbrella):
> ```
> "decision": "human_review",
> "reason": "reviewer_disagreement=['exclusions']",
> "confidence_summary": {..., "exclusions": 0.93, ...},
> "fields_below_threshold": [],
> "reviewer_disagreements": ["exclusions"],
> "integration_failures": []
> ```
> The reviewer signal drove this decision — not confidence. Every one of this record's confidence scores sits at or above 0.93 (`fields_below_threshold: []`), and integration checks passed clean too. The only reason it was routed to human_review is `reviewer_disagreements: ["exclusions"]` — an independent second pass flagged that the extracted exclusion clause didn't match the source document, despite the extractor itself being highly confident. If the router trusted confidence alone, this record would have been auto_approved — a 0.93 self-rating clears the 0.90 threshold on every field. That would have shipped a wrong exclusion clause with no human ever seeing it. This is the same failure mode calibration-report.txt already surfaced independently: the (umbrella, exclusions) cell showed conf=0.93 but acc=0.00 across 2 real samples — this routing record and that calibration cell corroborate each other, both pointing at umbrella/exclusions as a slice where the model's stated confidence cannot be trusted on its own.

**1c. Where the aggregate lies.**
> From calibration-report.txt:
> ```
> umbrella  exclusions      n=2 conf=0.93 acc=0.00 brier=0.865
> OVERALL brier=0.291
> ```
> The `(umbrella, exclusions)` cell has mean predicted confidence 0.93 but observed accuracy 0.00 — the model was confidently wrong on both of its two umbrella-exclusions samples, driving a cell-level Brier score of 0.865 versus an overall Brier of only 0.291. Slicing by `policy_type × field` catches exactly what the single overall number hides: the aggregate 0.291 looks like a moderately well-calibrated system overall, but that average is propped up by clean cells like `(auto, premium_amount)` at acc=1.00/brier=0.003 — the umbrella/exclusions failure would be invisible in the overall figure alone, and a system trusting confidence uniformly across policy types would keep auto-approving umbrella exclusions it gets wrong every time.

---

## 2. Schema-enforced two-pass extraction

| Evidence | Value |
|---|---|
| Passing test count | 25 passed — 02-mortgage-extraction/tests.txt |
| Static analysis | mypy: "Success: no issues found in 11 source files" (02-mortgage-extraction/checks-mypy.txt); ruff: "All checks passed!" (02-mortgage-extraction/checks-ruff.txt) |
| Document run | income_sum_mismatch.txt (discrepancy-run.txt), income_missing_bonus.txt (extract-run.txt), appraisal_informal_sqft.txt (normalized-integer.txt) |
| Classified type | `income_verification` (income_sum_mismatch.txt, income_missing_bonus.txt); `appraisal` (appraisal_informal_sqft.txt) — confirmed via `classify:` log line, captured with `--verbose` |

**2a. Two guarantees.**
> From discrepancy-run.txt:
> ```
> classify: model=claude-haiku-4-5 in=1612 out=96 type=income_verification
> extract: model=claude-haiku-4-5 in=3771 out=199 tool=extract_income_verification
> ...
> "validation": {
>   "consistent": false,
>   "discrepancies": [
>     {"field": "total_monthly_income", "calculated": 9642.17,
>      "stated": 10892.17, "delta": -1250.0}
>   ]
> }
> ```
> The document was classified as `income_verification` and routed to `extract_income_verification` — a forced tool call, so the output shape (every field present, correctly typed) was already guaranteed before the validator ever ran. That guarantee cannot catch whether the *values* inside that valid shape are internally consistent. The validator catches the opposite: it re-derives total_monthly_income from the line items and cross-checks it against the stated total, catching the $1250 discrepancy above that a schema/tool-choice check alone would have passed as "valid." One error each can't catch: schema enforcement can't catch a mathematically wrong total; the consistency validator can't catch a single field that's simply wrong with nothing to cross-check it against.

**2b. Refusing to fabricate.**
> From extract-run.txt (income_missing_bonus.txt):
> ```
> "bonus_monthly": null,
> "bonus_ytd": null,
> ...
> "validation": {"consistent": true, "discrepancies": []}
> ```
> Null instead of an invented value, because the schema marks these fields nullable rather than required — per `test_ac_01_04` in test_us01_schema.py (02-mortgage-extraction/tests.txt), `income.bonus_ytd` is confirmed nullable, and the system prompt rule quoted in test_us03_prompts.py states: "Return null for any field not explicitly stated in the document. Do not infer, default, or fabricate." The schema gives the model a legitimate way to say "not stated" instead of forcing a plausible-looking invented number to satisfy a required-field constraint.

**2c. Normalization.**
> Source text, from appraisal_informal_sqft.txt:
> `"Gross Living Area:   approximately 2,400 sq ft (above-grade finished)"`
> Extracted value, from normalized-integer.txt:
> `"gross_living_area_sqft": 2400`
> Normalizing at extraction time — not downstream — means every consumer of the extracted record (the validator, routing, any later calculation) can treat this field as a plain integer immediately, without each one re-implementing its own "strip commas and the word approximately" logic. Confirmed by `prompts.NORMALIZATION_RULES` in test_us03_prompts.py, which is injected into every extractor system prompt and explicitly pairs "2,400" → "2400" as a worked example — the rule is centralized once, at the point of extraction, rather than scattered across downstream consumers.

---

## 3. Multi-source synthesis

| Evidence | Value |
|---|---|
| Passing test count | 34 passed — 03-supply-chain/tests.txt |
| Static analysis | mypy: "Success: no issues found in 8 source files" (03-supply-chain/static-checks-mypy.txt); ruff: "All checks passed!" (03-supply-chain/static-checks-ruff.txt) |
| Briefing file | investigate-run.txt |
| Section the conflict landed in | Contested |

**3a. Annotate, don't arbitrate.**
> From investigate-run.txt, Contested section:
> ```
> on_time_delivery_rate — 95.0 percent — supplier_audit (as of 2026-04-10)
>                          78.0 percent — logistics (as of 2026-04-05)
> ```
> A reader is better served by seeing both values than a single reconciled number (e.g. an averaged 86.5%) because the two sources may be measuring different things (e.g. a formal audit period vs. a rolling logistics window) — collapsing them hides that there's a real question to investigate, while preserving both tells the reader exactly which claim to go verify and against which source.

**3b. Source goes dark.**
> From timeout-run.txt:
> ```
> > Sources unavailable: logistics unavailable (timeout)
> ...
> ### late_shipment_count  _[missing source: timeout reading logistics]_
> - missing source: timeout reading logistics
> ```
> "Unreachable" is annotated with a distinct `missing source: timeout reading logistics` tag and named in the header, whereas "nothing to report" would just be a metric with zero claims and no failure note. The run still finishes because the failure is scoped to one reader — per `test_single_failure_does_not_abort` in test_coordinator.py (part of the 34 passed in 03-supply-chain/tests.txt), the other three sources (supplier_audit, internal_quality, industry_news) completed independently, so the coordinator proceeds on partial results rather than treating one reader's failure as fatal.

**3c. Dates as a guardrail.**
> From investigate-run.txt, average_lead_time_days:
> ```
> 12.0 days — supplier_audit (as of 2026-04-10)
> 12.0 days — logistics (as of 2026-04-05)
> ```
> Both sources report the same value on different dates, five days apart. Requiring a date is what lets the system correctly read this as two independent observations that happen to agree (Well-Established corroboration), rather than either a contradiction or one stale value echoed twice — the date is the signal that distinguishes "confirmed twice" from "quoted twice."

---

## 4. Synthesis

**4a. One principle.**
> System 1, corroborated across two independent artifacts: calibration-report.txt's `(umbrella, exclusions)` cell (conf=0.93, acc=0.00, brier=0.865, n=2) and routing_decisions.json's record POL-2025-103 (confidence 0.93 on `exclusions`, but reviewer disagreement present). A design that trusted the model's self-reported confidence at face value would have auto-approved both — the calibration cell's real samples and this routing record's synthetic-but-real one. Measuring observed accuracy and running an independent review against stated confidence — rather than trusting the stated confidence — is what caught it in both cases.

**4b. Confidence ≠ correctness.**
> Same evidence, System 1: `conf=0.93` next to `acc=0.00` (calibration-report.txt) is as direct a counter-example as this evidence pack offers — a model expressing 93% self-confidence while being wrong 100% of the time on that slice. It mattered most here specifically because System 1's routing logic (per test_ac_04_06 in 01-policy-pipeline/tests.txt, "high_confidence_plus_reviewer_disagreement_still_routes_to_human_review") already treats confidence as one signal among several rather than the sole gate — POL-2025-103 in routing_decisions.json is the concrete, generated evidence for *why* that design choice is correct, not just a defensible precaution.

**4c. Apply it.**
> For a workflow where an LLM pulls structured data from messy vendor invoices before they hit an accounting system, I'd reach for validated retry with escalation first: format/consistency errors (a typo'd total) are worth one re-prompt, but a field genuinely absent from the source invoice should escalate immediately rather than retry, exactly as System 1's `missing_source` branch does (perturbation-log.md, System 1: 1 API call, no retry). What I'd instrument: a calibration report sliced by (vendor_type × field), the same shape as calibration-report.txt, run periodically — the umbrella/exclusions cell here shows a single overall accuracy number can hide a systematically broken slice, and that's precisely the kind of drift I'd want an alert on before it silently degrades one document category.