from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, Path
import httpx
from app.core.settings import settings
from app.auth.token_store import TokenStore
from app.auth.partner_tokens import get_partner_token_cached
from app.auth.oauth_third_party import ensure_user_access_token
from app.tesla.client import TeslaClient
from app.schemas.fleet_proxy import FleetProxyRequest, FleetProxyResponse

router = APIRouter(prefix="/fleet", tags=["fleet"])

def get_store() -> TokenStore:
    return TokenStore(settings.REDIS_URL)

def user_client_or_401(token: str | None):
    if not token:
        raise HTTPException(status_code=401, detail="No user token. Call /api/auth/login first.")
    return TeslaClient(access_token=token)

@router.get("/status")
async def fleet_status(store: TokenStore = Depends(get_store)):
    try:
        token = await get_partner_token_cached(store)
        client = TeslaClient(access_token=token)
        return await client.status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Fleet status error: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fleet status error: {e}")

@router.get("/vehicles")
async def fleet_vehicles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    store: TokenStore = Depends(get_store),
):
    try:
        # 1) si on a un token utilisateur (third-party), on l'utilise
        user_token = await ensure_user_access_token()
        if user_token:
            client = TeslaClient(access_token=user_token)
            return await client.vehicles_list(page=page, page_size=page_size)

        # 2) sinon, on retombe sur le partner token (ATTENTION: 403 attendu ici)
        partner_token = await get_partner_token_cached(store)
        client = TeslaClient(access_token=partner_token)
        return await client.vehicles_list(page=page, page_size=page_size)

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Fleet vehicles error: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/partner/telemetry-errors")
async def partner_telemetry_errors(store: TokenStore = Depends(get_store)):
    """
    Récupère les erreurs de télémétrie de la flotte partenaire.
    Note: Cet endpoint nécessite un token partenaire (client_credentials) ET que l'application
    ait les permissions partenaire activées dans le portail Tesla Developer.
    Si tu obtiens 401 "Expected partner account token type", vérifie que :
    1. TESLA_CLIENT_ID et TESLA_CLIENT_SECRET sont bien configurés
    2. L'application a les permissions partenaire dans le portail Tesla Developer
    3. Le domaine partenaire est bien enregistré via /api/fleet/partner/register
    """
    try:
        token = await get_partner_token_cached(store)  # partner token requis
        client = TeslaClient(access_token=token)
        return await client.partner_fleet_telemetry_errors()
    except httpx.HTTPStatusError as e:
        error_detail = f"Partner telemetry error: {e}"
        # Si 401, donner plus de contexte
        if e.response and e.response.status_code == 401:
            error_detail += " - Vérifie que l'application a les permissions partenaire dans le portail Tesla Developer"
        raise HTTPException(status_code=502, detail=error_detail)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

# DEBUG: te permet de vérifier ton token partenaire
@router.get("/partner/token-debug")
async def partner_token_debug(store: TokenStore = Depends(get_store)):
    """
    Debug: Affiche les infos du token partenaire (scopes, audience, etc.)
    """
    from app.auth.partner_tokens import fetch_partner_token
    try:
        token_obj = await fetch_partner_token()
        return {
            "access_token_preview": token_obj.access_token[:12] + "...",
            "audience": settings.TESLA_AUDIENCE_EU,
            "auth_base": settings.TESLA_AUTH_BASE,
            "scopes": token_obj.scope,
            "expires_in": token_obj.expires_in,
            "token_type": token_obj.token_type,
        }
    except Exception as e:
        return {"error": str(e)}

@router.post("/vehicles/{vehicle_id}/wake")
async def fleet_wake(vehicle_id: str = Path(...),):
    try:
        user_token = await ensure_user_access_token()
        client = user_client_or_401(user_token)
        return await client.wake_up(vehicle_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Wake error: {e}")

@router.post("/vehicles/{vehicle_id}/lock")
async def fleet_lock(vehicle_id: str = Path(...),):
    try:
        user_token = await ensure_user_access_token()
        client = user_client_or_401(user_token)
        return await client.door_lock(vehicle_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Lock error: {e}")

@router.post("/vehicles/{vehicle_id}/unlock")
async def fleet_unlock(vehicle_id: str = Path(...),):
    try:
        user_token = await ensure_user_access_token()
        client = user_client_or_401(user_token)
        return await client.door_unlock(vehicle_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Unlock error: {e}")

@router.post("/vehicles/{vehicle_id}/charge/start")
async def fleet_charge_start(vehicle_id: str = Path(...),):
    try:
        user_token = await ensure_user_access_token()
        client = user_client_or_401(user_token)
        return await client.charge_start(vehicle_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Charge start error: {e}")

@router.post("/vehicles/{vehicle_id}/charge/stop")
async def fleet_charge_stop(vehicle_id: str = Path(...),):
    try:
        user_token = await ensure_user_access_token()
        client = user_client_or_401(user_token)
        return await client.charge_stop(vehicle_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Charge stop error: {e}")
    
@router.post("/partner/register")
async def partner_register(store: TokenStore = Depends(get_store)):
    """
    Enregistre l'application dans la région courante (résout le 412).
    Nécessite un partner token (client-credentials).
    """
    try:
        token = await get_partner_token_cached(store)
        client = TeslaClient(access_token=token)

        domain = (getattr(settings, "APP_DOMAIN", None) or "").strip()
        if not domain:
            raise HTTPException(status_code=400, detail="APP_DOMAIN manquant dans la configuration")

        pk_url = getattr(settings, "PUBLIC_KEY_URL", None)
        data = await client.partner_register(domain=domain, public_key_url=pk_url)
        return {"ok": True, "register": data}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Partner register error: {e}")

@router.get("/partner/public-key")
async def partner_public_key(store: TokenStore = Depends(get_store)):
    """
    Récupère la clé publique enregistrée pour le domaine partenaire.
    Note: Cet endpoint nécessite des scopes que le token partenaire (client_credentials)
    n'a généralement pas. On utilise donc le token utilisateur qui contient les scopes.
    """
    # Utiliser le token utilisateur en priorité (il a les scopes nécessaires)
    user_token = await ensure_user_access_token()
    if user_token:
        try:
            client = TeslaClient(access_token=user_token)
            domain = (getattr(settings, "APP_DOMAIN", None) or "").strip()
            if not domain:
                raise HTTPException(status_code=400, detail="APP_DOMAIN manquant dans la configuration")
            return await client.partner_public_key(domain)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Partner public_key error: {e}")
    
    # Fallback sur token partenaire si pas de token utilisateur
    try:
        token = await get_partner_token_cached(store)
        client = TeslaClient(access_token=token)
        domain = (getattr(settings, "APP_DOMAIN", None) or "").strip()
        if not domain:
            raise HTTPException(status_code=400, detail="APP_DOMAIN manquant dans la configuration")
        return await client.partner_public_key(domain)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Partner public_key error: {e}")

@router.post("/proxy", response_model=FleetProxyResponse)
async def fleet_proxy(payload: FleetProxyRequest, store: TokenStore = Depends(get_store)):
    """
    Proxy générique vers la Fleet API pour couvrir l'ensemble des endpoints.
    """
    audience = settings.TESLA_AUDIENCE_EU if payload.region == "eu" else settings.TESLA_AUDIENCE_NA
    if payload.token_type == "user":
        token = await ensure_user_access_token()
        if not token:
            raise HTTPException(status_code=401, detail="Token utilisateur manquant. Complète le flux OAuth via /api/auth/login.")
    else:
        token = await get_partner_token_cached(store)

    client = TeslaClient(base_url=audience, access_token=token)
    try:
        resp = await client.request(
            payload.method,
            payload.path,
            json=payload.json,
            params=payload.params,
            allow_error=True,
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Fleet proxy request error: {e}")

    try:
        body: object = resp.json()
    except ValueError:
        body = resp.text

    return FleetProxyResponse(
        status_code=resp.status_code,
        headers=dict(resp.headers),
        body=body,
    )