"""API tests for case management endpoints."""

import logging

from fastapi.testclient import TestClient

from app.api.routes import cases as cases_routes


def case_payload(case_number: str = "CASE-001") -> dict[str, str]:
    return {
        "case_number": case_number,
        "title": "Unable to reset password",
        "description": "Customer receives an error after submitting the password reset form.",
        "status": "open",
        "priority": "medium",
    }


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_case(client: TestClient) -> None:
    response = client.post("/cases", json=case_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["case_number"] == "CASE-001"
    assert body["title"] == "Unable to reset password"
    assert body["created_at"]
    assert body["updated_at"]


def test_create_case_rejects_invalid_data(client: TestClient) -> None:
    payload = case_payload()
    payload["status"] = "pending"

    response = client.post("/cases", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "status"]


def test_get_existing_case(client: TestClient) -> None:
    created = client.post("/cases", json=case_payload())
    case_id = created.json()["id"]

    response = client.get(f"/cases/{case_id}")

    assert response.status_code == 200
    assert response.json()["case_number"] == "CASE-001"


def test_get_nonexistent_case_returns_404(client: TestClient) -> None:
    response = client.get("/cases/999")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "CASE_NOT_FOUND", "message": "Case not found"}
    }


def test_list_cases(client: TestClient) -> None:
    client.post("/cases", json=case_payload("CASE-001"))
    client.post("/cases", json=case_payload("CASE-002"))

    response = client.get("/cases")

    assert response.status_code == 200
    assert [case["case_number"] for case in response.json()] == [
        "CASE-001",
        "CASE-002",
    ]


def test_update_existing_case(client: TestClient) -> None:
    created = client.post("/cases", json=case_payload())
    case_id = created.json()["id"]

    response = client.patch(
        f"/cases/{case_id}",
        json={
            "title": "Password reset issue resolved",
            "status": "resolved",
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Password reset issue resolved"
    assert response.json()["status"] == "resolved"


def test_update_nonexistent_case_returns_404(client: TestClient) -> None:
    response = client.patch(
        "/cases/999", json={"title": "Payment failure investigation"}
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "CASE_NOT_FOUND", "message": "Case not found"}
    }


def test_duplicate_case_number_returns_409(client: TestClient) -> None:
    client.post("/cases", json=case_payload())

    response = client.post("/cases", json=case_payload())

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "DUPLICATE_CASE_NUMBER",
            "message": "Case number already exists",
        }
    }


def test_unexpected_error_returns_generic_logged_response(
    client: TestClient, monkeypatch, caplog
) -> None:
    def raise_unexpected_error(*args, **kwargs):
        raise RuntimeError("database password leaked")

    monkeypatch.setattr(cases_routes, "get_cases", raise_unexpected_error)

    with caplog.at_level(logging.ERROR):
        response = client.get("/cases")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Internal server error",
        }
    }
    assert "database password leaked" not in response.text
    assert "unexpected application error" in caplog.text