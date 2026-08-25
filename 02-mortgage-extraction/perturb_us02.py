"""
Deliberate perturbation for System 2, grounded in the real
income_sum_mismatch.txt replay run (discrepancy-run.txt).

Baseline from that run:
  base_monthly=5416.67, bonus_monthly=1250.0, commission_monthly=2140.0,
  overtime_monthly=385.5, other_monthly=450.0
  calculated total = 9642.17
  stated_monthly_total (as extracted) = 10892.17  -> delta -1250.0, flagged

Perturbation: take the SAME line items, but edit stated_monthly_total to
sit just $1.50 above the true calculated sum (9642.17 + 1.50 = 9643.67)
instead of the document's actual $1250 error. This tests the exact
tolerance boundary (test_ac_04_02_default_tolerance_is_one_dollar shows
$1.00 passes, $1.50 fails) using real fixture numbers rather than
invented ones.
"""
from mortgage_extractor.models import Borrower, Income, MortgageExtraction
from mortgage_extractor.validator import validate

CALCULATED_TOTAL = 5416.67 + 1250.0 + 2140.0 + 385.5 + 450.0  # 9642.17, matches discrepancy-run.txt

# Exactly matching -> consistent (sanity check against the real fixture's own math)
exact = MortgageExtraction(
    borrower=Borrower(full_name="Marcus T. Hollingsworth"),
    income=Income(
        base_monthly=5416.67, bonus_monthly=1250.0, commission_monthly=2140.0,
        overtime_monthly=385.5, other_monthly=450.0,
        stated_monthly_total=CALCULATED_TOTAL,
    ),
)

# Perturbation: same real line items, stated total edited to just cross tolerance
perturbed = MortgageExtraction(
    borrower=Borrower(full_name="Marcus T. Hollingsworth"),
    income=Income(
        base_monthly=5416.67, bonus_monthly=1250.0, commission_monthly=2140.0,
        overtime_monthly=385.5, other_monthly=450.0,
        stated_monthly_total=round(CALCULATED_TOTAL + 1.50, 2),  # <-- edited
    ),
)

print(f"calculated_total (from real fixture line items): {CALCULATED_TOTAL}")

print("\n--- Exact match (stated == calculated) ---")
r1 = validate(exact)
print(f"consistent: {r1.consistent}, discrepancies: {r1.discrepancies}")

print(f"\n--- Perturbed: stated_monthly_total edited to {round(CALCULATED_TOTAL + 1.50, 2)} (+$1.50) ---")
r2 = validate(perturbed)
print(f"consistent: {r2.consistent}")
for d in r2.discrepancies:
    print(f"  field={d.field} calculated={d.calculated} stated={d.stated} delta={d.delta}")
