"""
Endpoints SUPABASE - Accès direct aux données Supabase sans passer par Tesla.
Ces endpoints permettent de récupérer les données depuis le cache Supabase uniquement.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from app.auth.supabase_auth import require_supabase_user
from app.services.vehicle_cache import VehicleCacheService
from typing import Optional

router = APIRouter(
    prefix="/fleet/supabase",
    tags=["fleet-supabase"],
    dependencies=[Depends(require_supabase_user)],
)

def get_cache_service() -> VehicleCacheService:
    """Retourne le service de cache des véhicules."""
    return VehicleCacheService()


@router.get("/vehicles")
async def supabase_vehicles(
    account_name: Optional[str] = Query(default=None, description="Nom du compte Tesla"),
    state: Optional[str] = Query(default=None, description="Filtrer par état (online, offline, asleep)"),
    max_age_minutes: int = Query(default=60, ge=1, le=1440, description="Âge maximum accepté du cache en minutes"),
    user_info: dict = Depends(require_supabase_user),
    cache: VehicleCacheService = Depends(get_cache_service),
):
    """
    Récupère la liste des véhicules depuis Supabase uniquement (pas d'appel à Tesla).
    Retourne les données du cache si disponibles et non expirées.
    """
    user_id = user_info.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="ID utilisateur introuvable")
    
    account_id = cache.get_active_tesla_account(user_id, account_name)
    if not account_id:
        raise HTTPException(
            status_code=404,
            detail="Aucun compte Tesla trouvé. Utilisez /fleet/sync/sync pour synchroniser d'abord."
        )
    
    vehicles = cache.get_cached_vehicles(account_id, max_age_minutes=max_age_minutes, state=state)
    
    if vehicles is None:
        raise HTTPException(
            status_code=404,
            detail="Aucune donnée en cache. Utilisez /fleet/sync/sync pour synchroniser avec Tesla."
        )
    
    return {
        "response": vehicles,
        "count": len(vehicles),
        "source": "supabase_cache",
    }


@router.get("/vehicles/{vehicle_id}/data/{endpoint_name}")
async def supabase_vehicle_endpoint(
    vehicle_id: str = Path(..., description="ID Tesla du véhicule (tesla_id)"),
    endpoint_name: str = Path(..., description="Nom de l'endpoint (ex: charge_state, vehicle_state)"),
    account_name: Optional[str] = Query(default=None, description="Nom du compte Tesla"),
    user_info: dict = Depends(require_supabase_user),
    cache: VehicleCacheService = Depends(get_cache_service),
):
    """
    Récupère les données d'un endpoint spécifique depuis Supabase uniquement (pas d'appel à Tesla).
    Retourne les données du cache si disponibles et non expirées.
    """
    user_id = user_info.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="ID utilisateur introuvable")
    
    account_id = cache.get_active_tesla_account(user_id, account_name)
    if not account_id:
        raise HTTPException(status_code=404, detail="Aucun compte Tesla trouvé")
    
    vehicle_uuid = cache.get_vehicle_by_tesla_id(account_id, vehicle_id)
    if not vehicle_uuid:
        raise HTTPException(
            status_code=404,
            detail=f"Véhicule {vehicle_id} non trouvé. Utilisez /fleet/sync/sync pour synchroniser."
        )
    
    cached_data = cache.get_cached_endpoint(vehicle_uuid, endpoint_name)
    if not cached_data:
        raise HTTPException(
            status_code=404,
            detail=f"Données non disponibles en cache. Utilisez /fleet/sync/vehicles/{vehicle_id}/data/{endpoint_name} pour synchroniser."
        )
    
    return {
        "response": cached_data,
        "source": "supabase_cache",
    }


@router.get("/accounts")
async def supabase_accounts(
    user_info: dict = Depends(require_supabase_user),
    cache: VehicleCacheService = Depends(get_cache_service),
):
    """
    Liste tous les comptes Tesla d'un utilisateur depuis Supabase.
    """
    user_id = user_info.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="ID utilisateur introuvable")
    
    # Accéder directement au client Supabase du service
    result = cache.supabase.table('tesla_accounts')\
        .select('*')\
        .eq('supabase_user_id', user_id)\
        .order('created_at', desc=False)\
        .execute()
    
    return {
        "accounts": result.data,
        "count": len(result.data),
    }

