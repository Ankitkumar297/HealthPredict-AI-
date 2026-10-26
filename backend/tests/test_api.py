import os
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch
import httpx
import pytest

os.environ["DATABASE_URL"] = "sqlite:///./test_healthpredict.db"
from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.ai import AssessmentFailure  # noqa: E402
from app.ai import assess_blood_values  # noqa: E402

class LocalClient:
    def request(self, method, path, **kwargs):
        async def run():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
                return await client.request(method, path, **kwargs)
        return asyncio.run(run())

    def get(self, path):
        return self.request("GET", path)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def delete(self, path):
        return self.request("DELETE", path)


client = LocalClient()
VALID = {"full_name": "Test Person", "date_of_birth": "28/01/1960", "email": "test@example.com", "glucose": 100, "haemoglobin": 13.5, "cholesterol": 180}


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


def test_crud_and_duplicate_policy():
    first = client.post("/api/patients", json=VALID)
    assert first.status_code == 201
    second = client.post("/api/patients", json=VALID)
    assert second.status_code == 201 and second.json()["id"] != first.json()["id"]
    patient_id = first.json()["id"]
    assert len(client.get("/api/patients").json()) == 2
    assert client.get(f"/api/patients/{patient_id}").json()["full_name"] == "Test Person"
    updated = client.put(f"/api/patients/{patient_id}", json={**VALID, "email": "gokul@infocare.com"})
    assert updated.status_code == 200 and updated.json()["email"] == "gokul@infocare.com"
    assert client.delete(f"/api/patients/{patient_id}").status_code == 204
    assert client.get(f"/api/patients/{patient_id}").status_code == 404
    assert len(client.get("/api/patients").json()) == 1


@pytest.mark.parametrize("changes,field", [
    ({"email":"hunter@gmail"},"email"),
    ({"date_of_birth":"31/11/2001"},"date_of_birth"),
    ({"date_of_birth":"19/10/2030"},"date_of_birth"),
    ({"glucose":-1},"glucose"),
    ({"haemoglobin":"NaN"},"haemoglobin"),
    ({"cholesterol":None},"cholesterol"),
    ({"full_name":"   "},"full_name"),
])
def test_validation(changes, field):
    response = client.post("/api/patients", json={**VALID, **changes})
    assert response.status_code == 422
    assert any(e["field"] == field and e["input"] == changes[field] for e in response.json()["errors"])


def test_database_persistence():
    patient_id = client.post("/api/patients", json=VALID).json()["id"]
    engine.dispose()
    assert client.get(f"/api/patients/{patient_id}").status_code == 200


def test_ai_success_and_no_secrets():
    patient_id = client.post("/api/patients", json=VALID).json()["id"]
    with patch("app.main.assess_blood_values", new_callable=AsyncMock, return_value="Possible indicator. Informational only; this is not a medical diagnosis.") as mock:
        response = client.post(f"/api/patients/{patient_id}/assess")
    assert response.status_code == 200 and response.json()["ai_status"] == "completed"
    mock.assert_awaited_once_with(100.0, 13.5, 180.0)
    assert "ai_api_key" not in response.text.lower()


def test_ai_failure_does_not_fabricate():
    patient_id = client.post("/api/patients", json=VALID).json()["id"]
    with patch("app.main.assess_blood_values", new_callable=AsyncMock, side_effect=AssessmentFailure("AI provider timed out. Try again later.")):
        response = client.post(f"/api/patients/{patient_id}/assess")
    assert response.status_code == 503
    stored = client.get(f"/api/patients/{patient_id}").json()
    assert stored["ai_status"] == "failed" and stored["ai_remarks"] is None


def test_blood_update_clears_old_assessment():
    patient_id = client.post("/api/patients", json=VALID).json()["id"]
    with patch("app.main.assess_blood_values", new_callable=AsyncMock, return_value="Informational only; this is not a medical diagnosis."):
        client.post(f"/api/patients/{patient_id}/assess")
    changed = client.put(f"/api/patients/{patient_id}", json={**VALID,"glucose":101}).json()
    assert changed["ai_status"] == "pending" and changed["ai_remarks"] is None


@pytest.mark.parametrize("status_code,expected", [
    (401, "authentication failed"),
    (429, "rate limit reached"),
    (404, "model or endpoint is unavailable"),
])
def test_provider_http_errors(status_code, expected):
    async def run():
        def reply(request):
            assert "Synthetic" not in request.content.decode()
            return httpx.Response(status_code, json={"error": "provider test error"})
        transport = httpx.MockTransport(reply)
        with patch("app.ai.settings.ai_api_key", "test-only-key"), patch("app.ai.httpx.AsyncClient", return_value=httpx.AsyncClient(transport=transport)):
            with pytest.raises(AssessmentFailure, match=expected):
                await assess_blood_values(100, 13, 180)
    asyncio.run(run())


def test_provider_timeout():
    async def run():
        def timeout(request):
            raise httpx.ReadTimeout("test timeout", request=request)
        transport = httpx.MockTransport(timeout)
        with patch("app.ai.settings.ai_api_key", "test-only-key"), patch("app.ai.httpx.AsyncClient", return_value=httpx.AsyncClient(transport=transport)):
            with pytest.raises(AssessmentFailure, match="timed out"):
                await assess_blood_values(100, 13, 180)
    asyncio.run(run())


def test_exact_assessment_crud_walkthrough():
    rows = [
        ("Robyn Pears", "28.01.1960", "robyn@gmail.com", 232, 13.5, 180),
        ("John Hunter", "10.12.1990", "hunter@gmail", 94, 15, 200),
        ("Darryl Tim", "12.11.1993", "timd@smh.com.au", 240, 18.6, 326),
        ("Peter Larry", "31.11.2001", "Larry@hotmail.com", 88, 11.5, 165),
        ("Sam Kerr", "09.12.2006", "sam@news.com.au", 198, 8.9, 192),
        ("Robyn Pears", "28.01.1960", "robyn@gmail.com", 232, 13.5, 180),
        ("Madison XI", "12.09.1998", "madison@hotmail.com", 85, 7.6, 163),
        ("Kris Wu", "19.10.2030", "Kris.wu.gmail.com", 79, 16.5, 197),
        ("Tenille Singh", "30.11.1991", "Tenille@yahoo.com", 101, 15, 310),
        ("Prem Kumar", "28.04.1990", "prem@telstra.com", 155, 12.5, 265),
    ]
    accepted = []
    rejected = []
    for name, dob, email, glucose, haemoglobin, cholesterol in rows:
        data = {"full_name": name, "date_of_birth": dob.replace(".", "/"), "email": email, "glucose": glucose, "haemoglobin": haemoglobin, "cholesterol": cholesterol}
        response = client.post("/api/patients", json=data)
        if response.status_code == 201:
            accepted.append((data, response.json()["id"]))
        else:
            rejected.append((name, response.json()["errors"]))
    assert len(accepted) == 7 and len(rejected) == 3
    assert [item[0] for item in rejected] == ["John Hunter", "Peter Larry", "Kris Wu"]
    assert [[error["field"] for error in errors] for _, errors in rejected] == [
        ["email"], ["date_of_birth"], ["date_of_birth", "email"]
    ]
    assert [error["input"] for error in rejected[1][1]] == ["31/11/2001"]
    assert accepted[0][1] != accepted[3][1]  # Identical Robyn Pears rows receive distinct IDs.
    assert len(client.get("/api/patients").json()) == 7
    data, patient_id = accepted[0]
    updated = client.put(f"/api/patients/{patient_id}", json={**data, "email": "gokul@infocare.com"})
    assert updated.status_code == 200
    assert client.get(f"/api/patients/{patient_id}").json()["email"] == "gokul@infocare.com"
    assert client.delete(f"/api/patients/{patient_id}").status_code == 204
    assert len(client.get("/api/patients").json()) == 6


def teardown_module():
    engine.dispose()
    Path("test_healthpredict.db").unlink(missing_ok=True)
