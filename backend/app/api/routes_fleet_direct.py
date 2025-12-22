"""
Endpoints DIRECT - Appels directs à l'API Tesla sans cache.
Ces endpoints sont utilisés pour les actions qui nécessitent une réponse en temps réel.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Path
from app.auth.supabase_auth import require_supabase_user
from app.auth.oauth_third_party import ensure_user_access_token
from app.tesla.client import TeslaClient
from app.tesla.vcp import VCPError
import httpx

router = APIRouter(
    prefix="/fleet/direct",
    tags=["fleet-direct"],
    dependencies=[Depends(require_supabase_user)],
)


async def get_tesla_client(user_info: dict) -> TeslaClient:
    """
    Crée un client Tesla avec le token utilisateur.
    Lève une exception si le token n'est pas disponible.
    """
    user_id = user_info.get("user_id")
    user_token = await ensure_user_access_token(user_id=user_id)
    if not user_token:
        raise HTTPException(
            status_code=401,
            detail="Token Tesla utilisateur non trouvé. Complétez le flux OAuth via /api/auth/login."
        )
    return TeslaClient(access_token=user_token)


# ============================================================================
# ACTIONS VÉHICULE (Wake, Lock, Unlock, Charge)
# ============================================================================

@router.post("/vehicles/{vehicle_id}/wake")
async def direct_wake(
    vehicle_id: str = Path(...),
    user_info: dict = Depends(require_supabase_user),
):
    """
    Réveille un véhicule Tesla.
    Appel direct à l'API Tesla (pas de cache).
    """
    try:
        client = await get_tesla_client(user_info)
        return await client.wake_up(vehicle_id)
    except VCPError as e:
        raise HTTPException(status_code=502, detail=f"Erreur wake: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.post("/vehicles/{vehicle_id}/lock")
async def direct_lock(
    vehicle_id: str = Path(...),
    user_info: dict = Depends(require_supabase_user),
):
    """
    Verrouille un véhicule Tesla.
    Appel direct à l'API Tesla (pas de cache).
    """
    try:
        client = await get_tesla_client(user_info)
        return await client.door_lock(vehicle_id)
    except VCPError as e:
        raise HTTPException(status_code=502, detail=f"Erreur lock: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.post("/vehicles/{vehicle_id}/unlock")
async def direct_unlock(
    vehicle_id: str = Path(...),
    user_info: dict = Depends(require_supabase_user),
):
    """
    Déverrouille un véhicule Tesla.
    Appel direct à l'API Tesla (pas de cache).
    """
    try:
        client = await get_tesla_client(user_info)
        return await client.door_unlock(vehicle_id)
    except VCPError as e:
        raise HTTPException(status_code=502, detail=f"Erreur unlock: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.post("/vehicles/{vehicle_id}/charge/start")
async def direct_charge_start(
    vehicle_id: str = Path(...),
    user_info: dict = Depends(require_supabase_user),
):
    """
    Démarre la charge d'un véhicule Tesla.
    Appel direct à l'API Tesla (pas de cache).
    """
    try:
        client = await get_tesla_client(user_info)
        return await client.charge_start(vehicle_id)
    except VCPError as e:
        raise HTTPException(status_code=502, detail=f"Erreur charge start: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.post("/vehicles/{vehicle_id}/charge/stop")
async def direct_charge_stop(
    vehicle_id: str = Path(...),
    user_info: dict = Depends(require_supabase_user),
):
    """
    Arrête la charge d'un véhicule Tesla.
    Appel direct à l'API Tesla (pas de cache).
    """
    try:
        client = await get_tesla_client(user_info)
        return await client.charge_stop(vehicle_id)
    except VCPError as e:
        raise HTTPException(status_code=502, detail=f"Erreur charge stop: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


# ============================================================================
# PROXY GÉNÉRIQUE
# ============================================================================

@router.post("/proxy")
async def direct_proxy(
    method: str,
    path: str,
    json_body: dict = None,
    params: dict = None,
    region: str = None,
    user_info: dict = Depends(require_supabase_user),
):
    """
    Proxy générique vers l'API Tesla.
    Permet d'appeler n'importe quel endpoint Tesla directement.
    Appel direct (pas de cache).
    """
    from app.core.settings import settings
    from app.schemas.fleet_proxy import FleetProxyResponse
    
    user_id = user_info.get("user_id")
    user_token = await ensure_user_access_token(user_id=user_id)
    if not user_token:
        raise HTTPException(
            status_code=401,
            detail="Token Tesla utilisateur non trouvé."
        )
    
    audience = settings.tesla_audience_for(region)
    client = TeslaClient(base_url=audience, access_token=user_token)
    
    try:
        resp = await client.request(
            method,
            path,
            json=json_body,
            params=params,
            allow_error=True,
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Erreur proxy: {e}")
    
    try:
        body: object = resp.json()
    except ValueError:
        body = resp.text
    
    return FleetProxyResponse(
        status_code=resp.status_code,
        headers=dict(resp.headers),
        body=body,
    )

