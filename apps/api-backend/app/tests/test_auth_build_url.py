from app.auth.oauth_third_party import build_authorize_url
from app.core.settings import settings

def test_build_authorize_url(monkeypatch):
    monkeypatch.setattr(settings, "TP_CLIENT_ID", "cid", raising=False)
    monkeypatch.setattr(settings, "TP_REDIRECT_URI", "http://localhost:8000/api/auth/callback", raising=False)
    url = build_authorize_url(audience="https://fleet-api.prd.eu.vn.cloud.tesla.com")
    assert "/authorize?" in url
    assert "client_id=cid" in url
    assert "redirect_uri=" in url
    assert "audience=" in url