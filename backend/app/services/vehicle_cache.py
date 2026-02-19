"""
Service pour gérer le cache des véhicules dans Supabase.
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from supabase import create_client
from app.core.settings import settings
import json


class VehicleCacheService:
    """Service pour gérer le cache des véhicules et données Tesla dans Supabase."""
    
    def __init__(self):
        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.get_supabase_key_for_admin()
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL et SUPABASE_KEY doivent être configurés")
        
        self.supabase = create_client(supabase_url, supabase_key)
    
    def get_active_tesla_account(self, user_id: str, account_name: Optional[str] = None) -> Optional[str]:
        """
        Récupère le compte Tesla actif d'un utilisateur.
        
        Args:
            user_id: ID utilisateur Supabase
            account_name: Nom du compte (optionnel, utilise le premier actif si non fourni)
        
        Returns:
            UUID du compte Tesla ou None
        """
        query = self.supabase.table('tesla_accounts')\
            .select('id')\
            .eq('supabase_user_id', user_id)\
            .eq('is_active', True)
        
        if account_name:
            query = query.eq('account_name', account_name)
        
        result = query.order('created_at', desc=False).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]['id']
        return None
    
    def create_or_get_tesla_account(self, user_id: str, account_name: str = "Compte principal", email: Optional[str] = None) -> str:
        """
        Crée ou récupère un compte Tesla pour un utilisateur.
        
        Returns:
            UUID du compte Tesla
        """
        # Vérifier si le compte existe déjà
        existing = self.get_active_tesla_account(user_id, account_name)
        if existing:
            return existing
        
        # Créer un nouveau compte
        result = self.supabase.table('tesla_accounts').insert({
            'supabase_user_id': user_id,
            'account_name': account_name,
            'email': email,
            'is_active': True
        }).execute()
        
        return result.data[0]['id']
    
    def cache_vehicles(self, account_id: str, vehicles_data: List[Dict[str, Any]]) -> None:
        """
        Met en cache les données des véhicules.

        Les véhicules déjà en base pour ce compte mais absents de cette réponse
        (ex. véhicule en sommeil) ont leur last_synced_at rafraîchi pour rester
        visibles dans la liste.
        """
        now_iso = datetime.utcnow().isoformat()
        ids_in_response = []
        for vehicle in vehicles_data:
            vid = vehicle.get("id")
            if vid is not None:
                ids_in_response.append(vid)
            vehicle_data = {
                "tesla_account_id": account_id,
                "tesla_id": vehicle["id"],
                "tesla_vehicle_id": vehicle["vehicle_id"],
                "vin": vehicle["vin"],
                "vehicle_data": vehicle,
                "display_name": vehicle.get("display_name"),
                "access_type": vehicle.get("access_type"),
                "state": vehicle.get("state"),
                "in_service": vehicle.get("in_service", False),
                "api_version": vehicle.get("api_version"),
                "last_synced_at": now_iso,
            }
            existing = (
                self.supabase.table("vehicles")
                .select("id")
                .eq("tesla_account_id", account_id)
                .eq("tesla_id", vehicle["id"])
                .limit(1)
                .execute()
            )
            if existing.data and len(existing.data) > 0:
                self.supabase.table("vehicles").update(vehicle_data).eq("id", existing.data[0]["id"]).execute()
            else:
                self.supabase.table("vehicles").insert(vehicle_data).execute()
        # Garder visibles les véhicules du compte non retournés par Tesla (ex. en sommeil)
        if ids_in_response:
            # PostgREST .not_.in_() attend une chaîne du type "(val1,val2,...)"
            ids_tuple = "(" + ",".join(str(x) for x in ids_in_response) + ")"
            all_other = (
                self.supabase.table("vehicles")
                .select("id")
                .eq("tesla_account_id", account_id)
                .not_.in_("tesla_id", ids_tuple)
                .execute()
            )
            if all_other.data:
                for row in all_other.data:
                    self.supabase.table("vehicles").update({"last_synced_at": now_iso}).eq("id", row["id"]).execute()
    
    def get_cached_vehicles(
        self,
        account_id: str,
        max_age_minutes: Optional[int] = 5,
        state: Optional[str] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Récupère les véhicules depuis le cache.

        Args:
            account_id: UUID du compte Tesla
            max_age_minutes: Âge maximum du cache en minutes. None ou 0 = tous les
                véhicules du compte (pas de filtre d'âge), pour éviter qu'un véhicule
                absent d'une sync récente (ex. en sommeil) disparaisse de la liste.
            state: Filtrer par état (online, offline, asleep)

        Returns:
            Liste des véhicules ou None si le cache est expiré (uniquement si
            max_age_minutes est défini et qu'aucun véhicule n'est assez récent).
        """
        query = (
            self.supabase.table("vehicles")
            .select("vehicle_data")
            .eq("tesla_account_id", account_id)
        )
        if max_age_minutes and max_age_minutes > 0:
            cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
            query = query.gte("last_synced_at", cutoff_time.isoformat())
        if state:
            query = query.eq("state", state)
        result = query.execute()
        if result.data and len(result.data) > 0:
            return [item["vehicle_data"] for item in result.data]
        return None
    
    def cache_endpoint_response(
        self,
        account_id: str,
        vehicle_id: str,
        endpoint_name: str,
        response_data: Dict[str, Any],
        ttl_minutes: int = 5
    ) -> None:
        """
        Met en cache une réponse d'endpoint Tesla.
        
        Args:
            account_id: UUID du compte Tesla
            vehicle_id: UUID du véhicule dans la table vehicles
            endpoint_name: Nom de l'endpoint (ex: 'charge_state', 'vehicle_state')
            response_data: Données de la réponse
            ttl_minutes: Durée de vie du cache en minutes
        """
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        
        self.supabase.table('vehicle_data_cache').upsert({
            'tesla_account_id': account_id,
            'vehicle_id': vehicle_id,
            'endpoint_name': endpoint_name,
            'response_data': response_data,
            'expires_at': expires_at.isoformat(),
            'last_fetched_at': datetime.utcnow().isoformat()
        }).execute()
    
    def get_cached_endpoint(
        self,
        vehicle_id: str,
        endpoint_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Récupère une réponse d'endpoint depuis le cache.
        
        Args:
            vehicle_id: UUID du véhicule dans la table vehicles
            endpoint_name: Nom de l'endpoint
        
        Returns:
            Données de la réponse ou None si non trouvé/expiré
        """
        result = self.supabase.table('vehicle_data_cache')\
            .select('response_data')\
            .eq('vehicle_id', vehicle_id)\
            .eq('endpoint_name', endpoint_name)\
            .gt('expires_at', datetime.utcnow().isoformat())\
            .execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]['response_data']
        return None
    
    def get_vehicle_by_tesla_id(self, account_id: str, tesla_id: str) -> Optional[str]:
        """
        Récupère l'UUID d'un véhicule depuis son ID Tesla.
        
        Returns:
            UUID du véhicule dans la table vehicles ou None
        """
        result = self.supabase.table('vehicles')\
            .select('id')\
            .eq('tesla_account_id', account_id)\
            .eq('tesla_id', tesla_id)\
            .limit(1)\
            .execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]['id']
        return None

