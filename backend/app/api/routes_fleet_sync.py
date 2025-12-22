"""
Endpoints SYNC - Utilisent le cache Supabase pour récupérer les données.
Ces endpoints vérifient d'abord le cache, puis synchronisent avec Tesla si nécessaire.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from app.auth.supabase_auth import require_supabase_user
from app.auth.oauth_third_party import ensure_user_access_token
from app.tesla.client import TeslaClient
from app.services.vehicle_cache import VehicleCacheService
from typing import Optional
import httpx

router = APIRouter(
    prefix="/fleet/sync",
    tags=["fleet-sync"],
    dependencies=[Depends(require_supabase_user)],
)

def get_cache_service() -> VehicleCacheService:
    """Retourne le service de cache des véhicules."""
    return VehicleCacheService()


@router.get("/vehicles")
async def sync_vehicles(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    force_refresh: bool = Query(default=False, description="Forcer la synchronisation avec Tesla"),
    max_cache_age_minutes: int = Query(default=5, ge=1, le=60, description="Âge maximum du cache en minutes"),
    user_info: dict = Depends(require_supabase_user),
    cache: VehicleCacheService = Depends(get_cache_service),
):
    """
    Récupère la liste des véhicules depuis le cache Supabase.
    Synchronise automatiquement avec Tesla si le cache est expiré ou si force_refresh=True.
    """
    user_id = user_info.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="ID utilisateur introuvable")
    
    # Récupérer ou créer le compte Tesla
    account_id = cache.get_active_tesla_account(user_id)
    if not account_id:
        account_id = cache.create_or_get_tesla_account(user_id)
    
    # Vérifier le cache si pas de force refresh
    if not force_refresh:
        cached_vehicles = cache.get_cached_vehicles(account_id, max_age_minutes=max_cache_age_minutes)
        if cached_vehicles:
            # Paginer les résultats en mémoire
            start = (page - 1) * page_size
            end = start + page_size
            paginated = cached_vehicles[start:end]
            
            return {
                "response": paginated,
                "pagination": {
                    "previous": page - 1 if page > 1 else None,
                    "next": page + 1 if end < len(cached_vehicles) else None,
                    "current": page,
                    "per_page": page_size,
                    "count": len(cached_vehicles),
                    "pages": (len(cached_vehicles) + page_size - 1) // page_size,
                },
                "count": len(paginated),
                "cached": True,
            }
    
    # Synchroniser avec Tesla
    user_token = await ensure_user_access_token(user_id=user_id)
    if not user_token:
        raise HTTPException(
            status_code=401,
            detail="Token Tesla utilisateur non trouvé. Complétez le flux OAuth via /api/auth/login."
        )
    
    try:
        client = TeslaClient(access_token=user_token)
        result = await client.vehicles_list(page=page, page_size=page_size)
        
        # Mettre en cache tous les véhicules (pas seulement la page actuelle)
        # Pour cela, on récupère toutes les pages
        all_vehicles = []
        current_page = 1
        
        while True:
            page_result = await client.vehicles_list(page=current_page, page_size=page_size)
            vehicles = page_result.get("response", [])
            if not vehicles:
                break
            
            all_vehicles.extend(vehicles)
            
            # Vérifier s'il y a une page suivante
            pagination = page_result.get("pagination", {})
            if not pagination.get("next"):
                break
            
            current_page += 1
        
        # Mettre en cache tous les véhicules
        if all_vehicles:
            cache.cache_vehicles(account_id, all_vehicles)
        
        # Retourner la page demandée
        start = (page - 1) * page_size
        end = start + page_size
        paginated = all_vehicles[start:end] if start < len(all_vehicles) else []
        
        return {
            "response": paginated,
            "pagination": {
                "previous": page - 1 if page > 1 else None,
                "next": page + 1 if end < len(all_vehicles) else None,
                "current": page,
                "per_page": page_size,
                "count": len(all_vehicles),
                "pages": (len(all_vehicles) + page_size - 1) // page_size,
            },
            "count": len(paginated),
            "cached": False,
        }
        
    except httpx.HTTPStatusError as e:
        error_detail = f"Erreur lors de la synchronisation avec Tesla: {e}"
        if e.response and e.response.status_code == 403:
            error_detail += "\n\nErreur 403: Le token utilisé n'a pas les permissions nécessaires."
        raise HTTPException(status_code=502, detail=error_detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la synchronisation: {str(e)}")


@router.get("/vehicles/{vehicle_id}/data/{endpoint_name}")
async def sync_vehicle_endpoint(
    vehicle_id: str = Path(..., description="ID Tesla du véhicule (tesla_id)"),
    endpoint_name: str = Path(..., description="Nom de l'endpoint (ex: charge_state, vehicle_state)"),
    force_refresh: bool = Query(default=False, description="Forcer la synchronisation avec Tesla"),
    user_info: dict = Depends(require_supabase_user),
    cache: VehicleCacheService = Depends(get_cache_service),
):
    """
    Récupère les données d'un endpoint spécifique depuis le cache Supabase.
    Synchronise automatiquement avec Tesla si le cache est expiré ou si force_refresh=True.
    """
    user_id = user_info.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="ID utilisateur introuvable")
    
    account_id = cache.get_active_tesla_account(user_id)
    if not account_id:
        raise HTTPException(status_code=404, detail="Aucun compte Tesla trouvé")
    
    # Récupérer l'UUID du véhicule dans la table vehicles
    vehicle_uuid = cache.get_vehicle_by_tesla_id(account_id, vehicle_id)
    if not vehicle_uuid:
        raise HTTPException(status_code=404, detail=f"Véhicule {vehicle_id} non trouvé dans le cache")
    
    # Vérifier le cache si pas de force refresh
    if not force_refresh:
        cached_data = cache.get_cached_endpoint(vehicle_uuid, endpoint_name)
        if cached_data:
            return {
                "response": cached_data,
                "cached": True,
            }
    
    # Synchroniser avec Tesla
    user_token = await ensure_user_access_token(user_id=user_id)
    if not user_token:
        raise HTTPException(
            status_code=401,
            detail="Token Tesla utilisateur non trouvé."
        )
    
    try:
        client = TeslaClient(access_token=user_token)
        
        # Construire le chemin de l'endpoint
        endpoint_path = f"/api/1/vehicles/{vehicle_id}/{endpoint_name}"
        resp = await client.request("GET", endpoint_path)
        data = resp.json()
        
        # Mettre en cache la réponse
        cache.cache_endpoint_response(account_id, vehicle_uuid, endpoint_name, data, ttl_minutes=5)
        
        return {
            "response": data,
            "cached": False,
        }
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Erreur lors de la synchronisation: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.post("/sync")
async def sync_all(
    account_name: Optional[str] = Query(default=None, description="Nom du compte Tesla à synchroniser"),
    user_info: dict = Depends(require_supabase_user),
    cache: VehicleCacheService = Depends(get_cache_service),
):
    """
    Synchronise tous les véhicules et leurs données avec Tesla.
    Force la mise à jour du cache.
    """
    user_id = user_info.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="ID utilisateur introuvable")
    
    account_id = cache.get_active_tesla_account(user_id, account_name)
    if not account_id:
        account_id = cache.create_or_get_tesla_account(user_id, account_name or "Compte principal")
    
    user_token = await ensure_user_access_token(user_id=user_id)
    if not user_token:
        raise HTTPException(
            status_code=401,
            detail="Token Tesla utilisateur non trouvé."
        )
    
    try:
        client = TeslaClient(access_token=user_token)
        
        # Récupérer tous les véhicules
        all_vehicles = []
        page = 1
        page_size = 50
        
        while True:
            result = await client.vehicles_list(page=page, page_size=page_size)
            vehicles = result.get("response", [])
            if not vehicles:
                break
            
            all_vehicles.extend(vehicles)
            
            pagination = result.get("pagination", {})
            if not pagination.get("next"):
                break
            
            page += 1
        
        # Mettre en cache tous les véhicules
        if all_vehicles:
            cache.cache_vehicles(account_id, all_vehicles)
        
        return {
            "success": True,
            "vehicles_synced": len(all_vehicles),
            "account_id": account_id,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la synchronisation: {str(e)}")

