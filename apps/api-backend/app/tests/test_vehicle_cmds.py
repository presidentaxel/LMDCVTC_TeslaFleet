import pytest, httpx
from httpx import Request, Response
from fastapi.testclient import TestClient
from app.main import app
from app.core.settings import settings
from app.auth.tp_store import TPStore

@pytest.fixture(autouse=True)
def seed_user_token():
    # on simule un token utilisateur valide en mémoire
    TPStore.set_token({"access_token":"userTok","refresh_token":"rtok","expires_in":3600})

def make_fake_async_client(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    RealAsyncClient = httpx.AsyncClient
    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            self._c = RealAsyncClient(transport=transport)
        async def __aenter__(self): return self._c
        async def __aexit__(self, et, ev, tb): await self._c.aclose()
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

@pytest.mark.parametrize("route,pathkey", [
    ("/api/fleet/vehicles/123/wake", "TESLA_CMD_WAKE"),
    ("/api/fleet/vehicles/123/lock", "TESLA_CMD_LOCK"),
    ("/api/fleet/vehicles/123/unlock", "TESLA_CMD_UNLOCK"),
    ("/api/fleet/vehicles/123/charge/start", "TESLA_CMD_CHARGE_START"),
    ("/api/fleet/vehicles/123/charge/stop", "TESLA_CMD_CHARGE_STOP"),
])
def test_cmds(monkeypatch, route, pathkey):
    target_path = getattr(settings, pathkey).format(id="123")
    base = settings.TESLA_AUDIENCE_EU.rstrip("/")

    def dispatch(req: Request) -> Response:
        url = str(req.url)
        if url == f"{base}{target_path}":
            assert req.headers.get("Authorization") == "Bearer userTok"
            return Response(200, json={"result": True})
        return Response(404)

    make_fake_async_client(monkeypatch, dispatch)
    client = TestClient(app)
    r = client.post(route)
    assert r.status_code == 200
    assert r.json().get("result") is True