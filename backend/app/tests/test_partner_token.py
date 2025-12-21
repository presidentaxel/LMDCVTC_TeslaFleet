import pytest, httpx
from httpx import Response, Request
from app.auth.token_store import TokenStore
from app.auth.partner_tokens import get_partner_token_cached
from app.core.settings import settings

class DummyRedis:
    def __init__(self):
        self.store = {}
    def get(self, k): return self.store.get(k)
    def setex(self, k, ttl, v): self.store[k] = v

@pytest.fixture
def token_store(monkeypatch):
    ts = TokenStore("redis://localhost/0")
    # remplace le client Redis interne par un dummy en mémoire
    monkeypatch.setattr(ts, "r", DummyRedis())
    return ts

@pytest.mark.asyncio
async def test_partner_token_fetch(monkeypatch, token_store):
    # 1) Mock de l'endpoint /token
    def handler(request: Request) -> Response:
        assert str(request.url).endswith("/oauth2/v3/token")
        return Response(
            200,
            json={"access_token": "abc123", "token_type": "Bearer", "expires_in": 3600},
        )
    transport = httpx.MockTransport(handler)

    # 2) Patch des credentials directement sur l'instance settings
    monkeypatch.setattr(settings, "TESLA_CLIENT_ID", "id", raising=False)
    monkeypatch.setattr(settings, "TESLA_CLIENT_SECRET", "secret", raising=False)

    # 3) Remplacer httpx.AsyncClient par un wrapper qui force notre transport
    RealAsyncClient = httpx.AsyncClient
    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            # ignore args/kwargs, force transport=transport
            self._client = RealAsyncClient(transport=transport)
        async def __aenter__(self):
            return self._client
        async def __aexit__(self, exc_type, exc, tb):
            await self._client.aclose()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    # 4) Appel testé : doit récupérer le token et le mettre en cache
    token = await get_partner_token_cached(token_store)
    assert token == "abc123"