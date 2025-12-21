import pytest, httpx
from httpx import Request, Response
from fastapi.testclient import TestClient
from app.main import app
from app.core.settings import settings

# Dummy Redis memstore
class DummyRedis:
    def __init__(self): self.store = {}
    def get(self, k): return self.store.get(k)
    def setex(self, k, ttl, v): self.store[k] = v

@pytest.fixture(autouse=True)
def patch_redis_from_url(monkeypatch):
    from app.auth import token_store as ts

    class DummyRedis:
        def __init__(self): self.store = {}
        def get(self, k): return self.store.get(k)
        def setex(self, k, ttl, v): self.store[k] = v

    # Remplace redis.from_url() utilisé dans TokenStore.__init__
    monkeypatch.setattr(ts.redis, "from_url", lambda url, decode_responses=True: DummyRedis())

@pytest.mark.asyncio
async def test_vehicles_ok(monkeypatch):
    # Credentials sur l'instance settings (pas besoin de vrais)
    monkeypatch.setattr(settings, "TESLA_CLIENT_ID", "id", raising=False)
    monkeypatch.setattr(settings, "TESLA_CLIENT_SECRET", "secret", raising=False)

    vehicles_path = settings.TESLA_VEHICLES_PATH

    def dispatch(req: Request) -> Response:
        # 1) Auth token
        if str(req.url).endswith("/oauth2/v3/token"):
            return Response(200, json={"access_token":"tok","expires_in":3600,"token_type":"Bearer"})
        # 2) Fleet vehicles OK
        if str(req.url) == f"{settings.tesla_audience_for()}{vehicles_path}?page=1&page_size=50":
            assert req.headers.get("Authorization") == "Bearer tok"
            return Response(200, json={"vehicles": [{"id":"v1"}, {"id":"v2"}], "page":1, "page_size":50})
        return Response(404)

    transport = httpx.MockTransport(dispatch)

    # Patch AsyncClient pour utiliser notre transport
    RealAsyncClient = httpx.AsyncClient
    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            self._client = RealAsyncClient(transport=transport)
        async def __aenter__(self): return self._client
        async def __aexit__(self, et, ev, tb): await self._client.aclose()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    client = TestClient(app)
    r = client.get("/api/fleet/vehicles?page=1&page_size=50")
    assert r.status_code == 200
    data = r.json()
    assert "vehicles" in data and len(data["vehicles"]) == 2

@pytest.mark.asyncio
async def test_vehicles_region_redirect(monkeypatch):
    monkeypatch.setattr(settings, "TESLA_CLIENT_ID", "id", raising=False)
    monkeypatch.setattr(settings, "TESLA_CLIENT_SECRET", "secret", raising=False)

    vehicles_path = settings.TESLA_VEHICLES_PATH

    def dispatch(req: Request) -> Response:
        url = str(req.url)
        if url.endswith("/oauth2/v3/token"):
            return Response(200, json={"access_token":"tok","expires_in":3600,"token_type":"Bearer"})

        # Premier appel EU -> 421 avec Location (NA)
        if url == f"{settings.TESLA_AUDIENCE_EU}{vehicles_path}?page=1&page_size=50":
            return Response(421, headers={"Location": f"{settings.TESLA_AUDIENCE_NA}{vehicles_path}?page=1&page_size=50"})

        # Suivons la Location -> NA OK
        if url == f"{settings.TESLA_AUDIENCE_NA}{vehicles_path}?page=1&page_size=50":
            assert req.headers.get("Authorization") == "Bearer tok"
            return Response(200, json={"vehicles": [{"id":"na1"}], "page":1, "page_size":50})

        return Response(404)

    transport = httpx.MockTransport(dispatch)

    RealAsyncClient = httpx.AsyncClient
    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            self._client = RealAsyncClient(transport=transport)
        async def __aenter__(self): return self._client
        async def __aexit__(self, et, ev, tb): await self._client.aclose()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    client = TestClient(app)
    r = client.get("/api/fleet/vehicles?page=1&page_size=50")
    assert r.status_code == 200
    data = r.json()
    assert data["vehicles"][0]["id"] == "na1"