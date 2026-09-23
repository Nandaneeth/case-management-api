"""Local mock REST API for ETL policy-source testing."""

from fastapi import FastAPI


app = FastAPI(
	title="Customer Support Policy Mock API",
	description="Small local source for testing policy metadata ingestion.",
)


POLICY_UPDATES = [
	{
		"policy_id": "POL-001",
		"category_code": "CAT-001",
		"policy_version": "2026.09",
	},
	{
		"policy_id": "POL-002",
		"category_code": "CAT-002",
		"policy_version": "2026.08",
	},
	{
		"policy_id": "POL-003",
		"category_code": "CAT-003",
		"policy_version": "2026.09",
	},
	{
		"policy_id": "POL-005",
		"category_code": "CAT-005",
		"policy_version": "2026.10",
	},
]


@app.get("/api/policy-updates")
def get_policy_updates() -> list[dict[str, str]]:
	"""Return deterministic policy updates for ETL ingestion tests."""

	return POLICY_UPDATES


@app.get("/health")
def health_check() -> dict[str, str]:
	"""Report that the mock source is available."""

	return {"status": "healthy"}
