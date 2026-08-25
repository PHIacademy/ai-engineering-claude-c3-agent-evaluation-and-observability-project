"""
Deliberate perturbation for System 1.

Change: build a synthetic model response where `exclusions` (a different
required field than the one covered by the existing test suite, which uses
`endorsements`) is returned as null -- simulating a policy document that
never states its exclusion clauses. max_retries is left at the default (3)
so the safeguard, not the retry budget, has to be the reason the pipeline
stops early.
"""
from tests.conftest import RecordedClient, make_tool_use_message, load_policy_text
from policy_extractor.retry import extract_with_retry
from policy_extractor.records import RetryFutileEscalation

# Only ONE response is queued. If the pipeline tried to retry, RecordedClient
# would raise AssertionError("RecordedClient exhausted...") -- so a clean
# escalation with no exception is itself proof of a single call.
response = make_tool_use_message(
    "extract_policy",
    {
        "policy_type": "auto",
        "premium_amount": 1512.88,
        "deductible": 500.0,
        "coverage_limit": 300000.0,
        "endorsements": [],
        "exclusions": None,  # <-- perturbation: required field missing from source
        "confidence": {
            "policy_type": 0.95, "premium_amount": 0.95, "deductible": 0.95,
            "coverage_limit": 0.9, "endorsements": 0.9, "exclusions": 0.2,
        },
    },
)
client = RecordedClient([response])

result = extract_with_retry(
    client=client,
    policy_id="POL-2025-009",
    document_text=load_policy_text("POL-2025-009"),
    max_retries=3,
)

print(f"result type: {type(result).__name__}")
if isinstance(result, RetryFutileEscalation):
    print(f"field: {result.field}")
    print(f"detected_pattern: {result.detected_pattern}")
    print(f"category: {result.category}")
print(f"API calls made: {client.call_count}")
