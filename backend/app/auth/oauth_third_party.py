from __future__ import annotations
import base64, hashlib, os
import httpx, urllib.parse, secrets
from typing import Optional, Dict, Any
from app.core.settings import settings
from .tp_store import TPStore

def _generate_pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode("ascii")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge

def build_authorize_url(audience: str | None = None) -> str:
    """
    Construit l'URL /authorize (Tesla Fleet Auth) avec PKCE (S256).
    """
    if not (settings.TP_CLIENT_ID and settings.TP_REDIRECT_URI):
        raise RuntimeError("TP_CLIENT_ID/TP_REDIRECT_URI manquants")

    state = secrets.token_urlsafe(16)
    verifier, challenge = _generate_pkce_pair()
    TPStore.set_pkce_verifier(state, verifier)

    params = {
        "response_type": "code",
        "client_id": settings.TP_CLIENT_ID,
        "redirect_uri": settings.TP_REDIRECT_URI,
        "scope": settings.TP_SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "prompt": "login",
    }
    # Par défaut, cibler EU pour limiter les redirections 421.
    params["audience"] = audience or settings.tesla_audience_for()

    return f"{settings.TESLA_AUTH_BASE}/authorize?{urllib.parse.urlencode(params)}"

async def exchange_code_for_token(code: str, state: Optional[str]) -> Dict[str, Any]:
    """
    Échange le code contre access_token/refresh_token (PKCE).
    """
    if not (settings.TP_CLIENT_ID and settings.TP_REDIRECT_URI):
        raise RuntimeError("TP_CLIENT_ID/TP_REDIRECT_URI manquants")

    code_verifier = TPStore.pop_pkce_verifier(state or "")
    if not code_verifier:
        # En dernier recours, refuser pour respecter PKCE
        raise RuntimeError("PKCE verifier introuvable (state expiré ou invalide)")

    data = {
        "grant_type": "authorization_code",
        "client_id": settings.TP_CLIENT_ID,
        "code": code,
        "redirect_uri": settings.TP_REDIRECT_URI,
        "code_verifier": code_verifier,
    }
    if settings.TP_CLIENT_SECRET:
        data["client_secret"] = settings.TP_CLIENT_SECRET

    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.post(f"{settings.TESLA_AUTH_BASE}/token", data=data)
        resp.raise_for_status()
        return resp.json()

async def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    # Pour PKCE, pas besoin d'envoyer client_secret
    data = {
        "grant_type": "refresh_token",
        "client_id": settings.TP_CLIENT_ID,
        "refresh_token": refresh_token,
    }
    if settings.TP_CLIENT_SECRET:
        data["client_secret"] = settings.TP_CLIENT_SECRET

    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.post(f"{settings.TESLA_AUTH_BASE}/token", data=data)
        resp.raise_for_status()
        return resp.json()

async def ensure_user_access_token() -> Optional[str]:
    """
    Retourne un access_token utilisateur valide si disponible,
    sinon tente un refresh avec le refresh_token.
    """
    token = TPStore.get_access_token()
    if token:
        return token
    rtk = TPStore.get_refresh_token()
    if not rtk:
        return None
    newtok = await refresh_access_token(rtk)
    TPStore.set_token(newtok)
    return TPStore.get_access_token()