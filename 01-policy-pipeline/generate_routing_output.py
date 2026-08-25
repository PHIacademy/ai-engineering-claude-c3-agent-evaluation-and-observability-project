"""
Generates a real routing-decision output file (no API access needed --
route_extraction() and write_routing_decisions() are pure Python, no
model calls involved). Use this py to answer 1b of reflection-brief.md.

Grounded in calibration-report.txt: the (umbrella, exclusions) cell showed
conf=0.93 but acc=0.00 across 2 samples -- i.e. the model was confidently
wrong. Record #3 below models exactly that failure mode: high extractor
self-confidence, but a genuine reviewer disagreement on the same field,
so routing correctly overrides the confidence and sends it to human_review.
"""
from pathlib import Path

from policy_extractor.records import PolicyExtraction
from policy_extractor.reviewer import FieldAgreement, IntegrationFinding, ReviewResult
from policy_extractor.routing import (
    apply_stratified_spot_check,
    route_extraction,
    write_routing_decisions,
)

INTEGRATION_CLEAN = [
    IntegrationFinding(check_name="coverage_limit_exceeds_endorsement_sum",
                       status="pass", details=""),
    IntegrationFinding(check_name="endorsements_exclusions_non_contradiction",
                       status="pass", details=""),
]


def agree_all(fields: list[str]) -> ReviewResult:
    return ReviewResult(agreements={
        f: FieldAgreement(field=f, agreement="agree", reason=None, review_confidence=0.95)
        for f in fields
    })


REVIEW_FIELDS = ["policy_type", "premium_amount", "deductible",
                 "coverage_limit", "endorsements", "exclusions"]

# --- Record 1: clean auto policy, all signals clear -> auto_approve ---
rec1 = PolicyExtraction(
    policy_id="POL-2025-101", policy_type="auto",
    premium_amount=1512.88, deductible=500.0, coverage_limit=300000.0,
    endorsements=None, exclusions=["Nuclear hazard"], premium_components=None,
    confidence={"policy_type": 0.98, "premium_amount": 0.96, "deductible": 0.95,
                "coverage_limit": 0.95, "endorsements": 0.9, "exclusions": 0.94},
)
d1 = route_extraction(extraction=rec1, review=agree_all(REVIEW_FIELDS),
                       integration_findings=INTEGRATION_CLEAN)

# --- Record 2: home policy, one confidence below threshold -> human_review ---
rec2 = PolicyExtraction(
    policy_id="POL-2025-102", policy_type="home",
    premium_amount=2400.0, deductible=1000.0, coverage_limit=348000.0,
    endorsements=None, exclusions=["Flood"], premium_components=None,
    confidence={"policy_type": 0.95, "premium_amount": 0.65, "deductible": 0.9,
                "coverage_limit": 0.9, "endorsements": 0.9, "exclusions": 0.9},
)
d2 = route_extraction(extraction=rec2, review=agree_all(REVIEW_FIELDS),
                       integration_findings=INTEGRATION_CLEAN)

# --- Record 3: umbrella, HIGH confidence but reviewer disagrees on exclusions
#     -- mirrors the real (umbrella, exclusions) failure cell from
#     calibration-report.txt (conf=0.93, acc=0.00) -> human_review ---
rec3 = PolicyExtraction(
    policy_id="POL-2025-103", policy_type="umbrella",
    premium_amount=5200.0, deductible=2500.0, coverage_limit=5000000.0,
    endorsements=None, exclusions=["Watercraft over 26ft"], premium_components=None,
    confidence={"policy_type": 0.97, "premium_amount": 0.95, "deductible": 0.95,
                "coverage_limit": 0.95, "endorsements": 0.95, "exclusions": 0.93},
)
review3 = agree_all(REVIEW_FIELDS)
review3.agreements["exclusions"] = FieldAgreement(
    field="exclusions", agreement="disagree",
    reason="Document lists a watercraft exclusion at 22ft, not 26ft.",
    review_confidence=0.9,
)
d3 = route_extraction(extraction=rec3, review=review3,
                       integration_findings=INTEGRATION_CLEAN)

decisions = [d1, d2, d3]
decisions = apply_stratified_spot_check(decisions, sample_pct=0.34, seed=7)

out_path = Path("routing_decisions.json")
write_routing_decisions(decisions, out_path)

counts = {"auto_approve": 0, "human_review": 0, "spot_check": 0}
for d in decisions:
    counts[d.decision] += 1

print(f"Wrote {out_path} with {len(decisions)} records")
print(f"auto_approve={counts['auto_approve']} human_review={counts['human_review']} "
      f"spot_check={counts['spot_check']}")
print()
for d in decisions:
    if d.decision == "human_review":
        print(f"policy_id={d.policy_id} decision={d.decision}")
        print(f"  reason={d.reason}")
        print(f"  fields_below_threshold={d.fields_below_threshold}")
        print(f"  reviewer_disagreements={d.reviewer_disagreements}")
        print(f"  integration_failures={d.integration_failures}")
