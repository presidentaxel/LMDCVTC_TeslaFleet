from __future__ import annotations
import httpx
from pydantic import BaseModel
from app.core.settings import settings
from app.auth.token_store import TokenStore

PARTNER_CACHE_KEY = "tesla:partner_token:eu"

class PartnerToken(BaseModel):
    access_token: str
    token_type: str | None = "Bearer"
    expires_in: int
    scope: str | None = None

async def fetch_partner_token() -> PartnerToken:
    """
    Récupère un partner token via client_credentials.
    Note: Pour les endpoints partenaire, les scopes sont généralement déterminés
    par la configuration de l'application dans le portail Tesla Developer.
    """
    if not settings.TESLA_CLIENT_ID or not settings.TESLA_CLIENT_SECRET:
        raise RuntimeError("TESLA_CLIENT_ID/SECRET manquants dans l'env.")

    data = {
        "grant_type": "client_credentials",
        "client_id": settings.TESLA_CLIENT_ID,
        "client_secret": settings.TESLA_CLIENT_SECRET,
        "audience": settings.TESLA_AUDIENCE_EU,  # on commencera par EU
    }
    # Note: Pour client_credentials, les scopes sont généralement déterminés par
    # la configuration de l'app dans le portail, mais on peut essayer de les spécifier
    # si nécessaire (décommenter si besoin):
    # data["scope"] = "fleet:partner:read fleet:partner:write"

    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.post(f"{settings.TESLA_AUTH_BASE}/token", data=data)
        resp.raise_for_status()
        payload = resp.json()
        return PartnerToken(**payload)

async def get_partner_token_cached(store: TokenStore) -> str:
    """
    Retourne un access_token valide depuis Redis, sinon fetch + cache.
    """
    cached = store.get(PARTNER_CACHE_KEY)
    if store.valid(cached):
        return cached["access_token"]

    token = await fetch_partner_token()
    # marge de sécurité 60s
    ttl = max(60, int(token.expires_in) - 60)
    store.set(PARTNER_CACHE_KEY, token.model_dump(), ttl=ttl)
    return token.access_token