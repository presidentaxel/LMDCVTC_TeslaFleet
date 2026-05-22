import httpx
import pytest
from fastapi.testclient import TestClient

from app.auth.business_tokens import BUSINESS_CACHE_KEY, fetch_business_token
from app.core.settings import settings
from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_fetch_business_token_success(monkeypatch):
    monkeypatch.setattr(settings, "TESLA_CLIENT_ID", "0517a56f-d3fd-43f5-9b80-5e15b0488d5f", raising=False)
    monkeypatch.setattr(settings, "TESLA_CLIENT_SECRET", "secret", raising=False)

    class FakeResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "access_token": "biz-token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": "vehicle_cmds",
            }

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, data=None):
            assert url.endswith("/token")
            assert data.get("auth_code") == "test-auth-code-12345678"
            return FakeResp()

    monkeypatch.setattr(
        "app.auth.business_tokens.httpx.AsyncClient",
        lambda **kwargs: FakeClient(),
    )
    token = await fetch_business_token("test-auth-code-12345678")
    assert token.access_token == "biz-token"


def test_consent_guide():
    r = client.get("/api/business/consent-guide")
    assert r.status_code == 200
    data = r.json()
    assert len(data["steps"]) >= 5
    assert "tesla.com/teslaaccount/business" in data["steps"][0]["url"]


def test_business_status_without_token():
    r = client.get("/api/business/status")
    assert r.status_code == 200
    assert r.json()["token_active"] is False


def test_commands_catalog():
    r = client.get("/api/business/commands/catalog")
    assert r.status_code == 200
    assert "categories" in r.json()
