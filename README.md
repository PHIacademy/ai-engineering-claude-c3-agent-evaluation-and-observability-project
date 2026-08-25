# AI Engineering with Claude — Evaluation & Observability Project

This repository contains the evidence pack, perturbation log, and reflection for the
**Evaluation and Observability** project, covering three reference systems built across
the course [`cd15552 Claude AI Engineer Evaluation and Observability`](.).

Each system ships as a separate project in the course repo, one folder per system. Every
run below was executed from the `solution/` directory of that project's **final** exercise
(the `starter/` folders hold the fill-in exercises — the capstone runs the finished
`solution/`). Install with `pip install -e ".[dev]"` from inside the solution dir, which
puts the console command on your `PATH`.

| Evidence folder | Course project → final-exercise `solution/` | Console command |
|---|---|---|
| [`01-policy-pipeline/`](01-policy-pipeline/) | `Build a Validated, Routed Insurance Policy Extraction Pipeline/04-hitl-routing/solution/` | `policy-extractor` |
| [`02-mortgage-extraction/`](02-mortgage-extraction/) | `Build a Resilient Mortgage Document Extraction System/04-validate-mathematical-consistency/solution/` | `mortgage-extract` |
| [`03-supply-chain/`](03-supply-chain/) | `Investigate Supply Chain Risk with Multi-Source Synthesis/03-resilient-coordinator/solution/` | `supply-chain-investigate` |

No `ANTHROPIC_API_KEY` was available for this submission — every extraction/pipeline run
uses recorded/replay clients, and any live-only test is explicitly SKIPPED (visible in each
`tests.txt`). Where a rubric item required a live API call that couldn't be made, an
offline-equivalent substitute is used and called out explicitly in that item's own file or
in [`reflection-brief.md`](reflection-brief.md).

## Top-level files

- [`reflection-brief.md`](reflection-brief.md) — the completed reflection brief, answering every prompt with a citation to a specific artifact below.
- [`environment.txt`](environment.txt) — `python3 --version` + OS, and how the three per-project venvs were set up.
- [`perturbation-log.md`](perturbation-log.md) — one deliberate input/configuration change per system, the command run, the prediction, and the observed result, contrasted against the unperturbed run.

## Repository structure

- 📁 **01-policy-pipeline/**
  - [`calibration-report.txt`](01-policy-pipeline/calibration-report.txt) — sliced (policy_type × field) calibration report, output of `run_report.py`.
  - [`generate_routing_output.py`](01-policy-pipeline/generate_routing_output.py) — standalone script that calls `route_extraction()` / `apply_stratified_spot_check()` / `write_routing_decisions()` directly on three hand-constructed extraction records, producing a real `routing_decisions.json` without needing API access (no model calls involved — these are pure-Python functions).
  - [`perturb_us01.py`](01-policy-pipeline/perturb_us01.py) — perturbation script for System 1: builds a synthetic extractor response with a required field (`exclusions`) set to `null`, demonstrating the pipeline escalates to `RetryFutileEscalation` after exactly one API call instead of retrying.
  - [`perturbation.txt`](01-policy-pipeline/perturbation.txt) — captured output of `perturb_us01.py`.
  - [`routing_decisions.json`](01-policy-pipeline/routing_decisions.json) — the generated routing-decision output file, written by `generate_routing_output.py`. **Scope note:** built from three hand-constructed extraction records, not the bundled `data/policies/` document set — `route_extraction()`/`write_routing_decisions()` require no API access, but running the full pipeline over the actual bundled documents would require a live extraction pass this environment couldn't perform (see `routing-decisions-without-API-access.txt`).
  - [`routing-decisions-without-API-access.txt`](01-policy-pipeline/routing-decisions-without-API-access.txt) — note explaining the no-API-access substitution above: why `routing_decisions.json` was generated from hand-constructed records via `generate_routing_output.py` rather than a live `policy-extractor pipeline` run over the bundled documents.
  - [`routing-output.txt`](01-policy-pipeline/routing-output.txt) — captured stdout of `generate_routing_output.py`: record count, `auto_approve`/`human_review`/`spot_check` totals, and the full `human_review` records with their routing reasons.
  - [`run_report.py`](01-policy-pipeline/run_report.py) — runs the calibration report.
  - [`static-checks-mypy.txt`](01-policy-pipeline/static-checks-mypy.txt) — `mypy` output ("Success: no issues found in 11 source files").
  - [`static-checks-ruff.txt`](01-policy-pipeline/static-checks-ruff.txt) — `ruff` output ("All checks passed!").
  - [`tests.txt`](01-policy-pipeline/tests.txt) — full `pytest -v` output (45 passed, 3 skipped).
  - [`screenshots/`](01-policy-pipeline/screenshots/) — terminal log screenshots.

- 📁 **02-mortgage-extraction/**
  - [`discrepancy-run.txt`](02-mortgage-extraction/discrepancy-run.txt) — `mortgage-extract income_sum_mismatch.txt --mode replay -v` output; the validator reports a discrepancy (calculated 9642.17 vs stated 10892.17).
  - [`extract-run.txt`](02-mortgage-extraction/extract-run.txt) — `mortgage-extract income_missing_bonus.txt --mode replay -v` output; a missing field returns `null` rather than a fabricated value.
  - [`normalized-integer.txt`](02-mortgage-extraction/normalized-integer.txt) — `mortgage-extract appraisal_informal_sqft.txt --mode replay -v` output; shows the classified document type (`appraisal`) and `"approximately 2,400 sq ft"` normalized to the integer `2400`.
  - [`perturb_us02.py`](02-mortgage-extraction/perturb_us02.py) — perturbation script for System 2: reuses the real line items from `discrepancy-run.txt`, editing only `stated_monthly_total` to sit $1.50 above the true calculated sum, testing the validator's exact tolerance boundary.
  - [`static-checks-mypy.txt`](02-mortgage-extraction/static-checks-mypy.txt) — `mypy` output ("Success: no issues found in 11 source files").
  - [`static-checks-ruff.txt`](02-mortgage-extraction/static-checks-ruff.txt) — `ruff` output ("All checks passed!").
  - [`tests.txt`](02-mortgage-extraction/tests.txt) — full `pytest -v` output (25 passed).
  - [`screenshots/`](02-mortgage-extraction/screenshots/) — terminal log screenshots.

- 📁 **03-supply-chain/**
  - [`investigation-run.txt`](03-supply-chain/investigation-run.txt) — `supply-chain-investigate meridian --offline` output; the generated briefing, showing all three sections (Well-Established, Contested, Incomplete) populated. The CLI has no `--output` flag, so this stdout capture *is* the briefing — there is no separate briefing file.
  - [`timeout-run.txt`](03-supply-chain/timeout-run.txt) — `supply-chain-investigate meridian --offline --simulate-timeout` output; the `logistics` source fails, the run completes rather than aborting, and the failure is explicitly annotated (`Sources unavailable: logistics unavailable (timeout)`).
  - [`static-checks-mypy.txt`](03-supply-chain/static-checks-mypy.txt) — `mypy` output ("Success: no issues found in 8 source files").
  - [`static-checks-ruff.txt`](03-supply-chain/static-checks-ruff.txt) — `ruff` output ("All checks passed!").
  - [`tests.txt`](03-supply-chain/tests.txt) — full `pytest -v` output (34 passed).
  - [`screenshots/`](03-supply-chain/screenshots/) — terminal log screenshots.

## Summary

| System | Passing tests | Static analysis | Perturbation |
|---|---|---|---|
| [01-policy-pipeline](01-policy-pipeline/) | 45 passed, 3 skipped | mypy clean, ruff clean | `missing_source` halts retry after 1 call |
| [02-mortgage-extraction](02-mortgage-extraction/) | 25 passed | mypy clean, ruff clean | tolerance boundary crossed at +$1.50 |
| [03-supply-chain](03-supply-chain/) | 34 passed | mypy clean, ruff clean | `--simulate-timeout` masks a real contested conflict |

See [`reflection-brief.md`](reflection-brief.md) for the full write-up, and
[`perturbation-log.md`](perturbation-log.md) for each experiment in detail.
