from __future__ import annotations
import httpx
from pydantic import BaseModel
from app.core.settings import settings
from app.auth.token_store import TokenStore
from app.auth.supabase_store import SupabaseTokenStore
from typing import Union

PARTNER_CACHE_KEY = "tesla:partner_token:eu"

class PartnerToken(BaseModel):
    access_token: str
    token_type: str | None = "Bearer"
    expires_in: int
    scope: str | None = None

async def fetch_partner_token(use_tp_credentials: bool = False) -> PartnerToken:
    """
    Récupère un partner token via client_credentials.
    
    Args:
        use_tp_credentials: Si True, utilise TP_CLIENT_ID/SECRET au lieu de TESLA_CLIENT_ID/SECRET.
                           Utile si vous utilisez le même CLIENT_ID pour les deux types de tokens.
    
    Note: Pour les endpoints partenaire, les scopes sont généralement déterminés
    par la configuration de l'application dans le portail Tesla Developer.
    """
    # Utiliser TP credentials si demandé ou si TESLA credentials ne sont pas disponibles
    if use_tp_credentials or not settings.TESLA_CLIENT_ID or not settings.TESLA_CLIENT_SECRET:
        if not settings.TP_CLIENT_ID or not settings.TP_CLIENT_SECRET:
            raise RuntimeError(
                "TESLA_CLIENT_ID/SECRET ou TP_CLIENT_ID/SECRET manquants dans l'env. "
                "Configurez au moins un des deux."
            )
        client_id = settings.TP_CLIENT_ID
        client_secret = settings.TP_CLIENT_SECRET
    else:
        client_id = settings.TESLA_CLIENT_ID
        client_secret = settings.TESLA_CLIENT_SECRET

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": settings.tesla_audience_for(),  # audience par défaut selon la région
    }
    # Note: Pour client_credentials, les scopes sont généralement déterminés par
    # la configuration de l'app dans le portail, mais on peut essayer de les spécifier
    # si nécessaire (décommenter si besoin):
    # data["scope"] = "fleet:partner:read fleet:partner:write"

    # Utiliser AUTH_TOKEN_BASE pour /token (fleet-auth.prd.vn.cloud.tesla.com)
    token_base = getattr(settings, "AUTH_TOKEN_BASE", None) or settings.TESLA_AUTH_BASE
    
    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.post(f"{token_base}/token", data=data)
        
        # Gérer les erreurs de manière plus détaillée
        if resp.status_code == 403:
            error_body = ""
            try:
                error_body = resp.json()
            except:
                error_body = resp.text[:500]
            
            raise RuntimeError(
                f"Tesla a refusé les credentials partenaires (403 Forbidden).\n\n"
                f"Causes possibles:\n"
                f"1. TESLA_CLIENT_ID/TESLA_CLIENT_SECRET ou TP_CLIENT_ID/TP_CLIENT_SECRET sont incorrects\n"
                f"2. L'application n'a pas les permissions partenaire dans le portail Tesla Developer\n"
                f"3. Les credentials sont pour un environnement différent (production vs staging)\n"
                f"4. Le domaine n'a pas encore été enregistré (peut être requis avant d'obtenir des tokens)\n"
                f"5. Vous utilisez peut-être les mauvais credentials - vérifiez que vous utilisez ceux du portail Tesla Developer\n\n"
                f"Votre CLIENT_ID devrait être: cacad6ff-48dd-4e8f-b521-8180d0865b94\n"
                f"CLIENT_ID utilisé: {client_id[:8]}...\n\n"
                f"Réponse Tesla: {error_body}"
            )
        elif resp.status_code == 401:
            error_body = ""
            try:
                error_body = resp.json()
            except:
                error_body = resp.text[:500]
            
            raise RuntimeError(
                f"Authentification partenaire échouée (401 Unauthorized).\n"
                f"Vérifiez que TESLA_CLIENT_ID/TESLA_CLIENT_SECRET ou TP_CLIENT_ID/TP_CLIENT_SECRET sont corrects.\n"
                f"CLIENT_ID utilisé: {client_id[:8]}...\n"
                f"Réponse Tesla: {error_body}"
            )
        
        resp.raise_for_status()
        payload = resp.json()
        return PartnerToken(**payload)

async def get_partner_token_cached(store: Union[TokenStore, SupabaseTokenStore], use_tp_credentials: bool = False) -> str:
    """
    Retourne un access_token valide depuis le store (Redis/Supabase), sinon fetch + cache.
    
    Args:
        store: Le store de tokens
        use_tp_credentials: Si True, utilise TP_CLIENT_ID/SECRET au lieu de TESLA_CLIENT_ID/SECRET
    """
    cached = store.get(PARTNER_CACHE_KEY)
    if store.valid(cached):
        return cached["access_token"]

    token = await fetch_partner_token(use_tp_credentials=use_tp_credentials)
    # marge de sécurité 60s
    ttl = max(60, int(token.expires_in) - 60)
    store.set(PARTNER_CACHE_KEY, token.model_dump(), ttl=ttl)
    return token.access_token
