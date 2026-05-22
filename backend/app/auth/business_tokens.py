"""Third-Party Business tokens (Tesla Fleet API)."""
from __future__ import annotations

import httpx
from pydantic import BaseModel

from app.core.settings import settings

BUSINESS_CACHE_KEY = "tesla:business_token"


class BusinessToken(BaseModel):
    access_token: str
    token_type: str | None = "Bearer"
    expires_in: int
    scope: str | None = None


def _client_credentials() -> tuple[str, str]:
    cid = settings.TESLA_CLIENT_ID or settings.TP_CLIENT_ID
    secret = settings.TESLA_CLIENT_SECRET or settings.TP_CLIENT_SECRET
    if not cid or not secret:
        raise RuntimeError(
            "TESLA_CLIENT_ID/SECRET manquants. Copiez-les depuis le portail Tesla Developer."
        )
    return cid, secret


def _token_payload(auth_code: str) -> dict[str, str]:
    cid, secret = _client_credentials()
    scopes = (settings.BUSINESS_SCOPES or settings.PARTNER_SCOPES).strip()
    return {
        "grant_type": "client_credentials",
        "client_id": cid,
        "client_secret": secret,
        "auth_code": auth_code,
        "audience": settings.tesla_audience_for(),
        "scope": scopes,
    }


async def fetch_business_token(auth_code: str) -> BusinessToken:
    """Échange un auth_code (Consent Management) contre un token business."""
    base = getattr(settings, "AUTH_TOKEN_BASE", None) or settings.TESLA_AUTH_BASE
    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.post(f"{base}/token", data=_token_payload(auth_code))
        if resp.status_code in (401, 403):
            body = resp.text[:500]
            raise RuntimeError(
                f"Tesla a refusé le token business ({resp.status_code}). "
                f"Vérifiez client_id/secret, auth_code non expiré, consentement approuvé. Détail: {body}"
            )
        resp.raise_for_status()
        return BusinessToken(**resp.json())
