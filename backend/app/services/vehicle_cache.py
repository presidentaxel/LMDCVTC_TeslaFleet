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
        
        Args:
            account_id: UUID du compte Tesla
            vehicles_data: Liste des données des véhicules depuis l'API Tesla
        """
        for vehicle in vehicles_data:
            vehicle_data = {
                'tesla_account_id': account_id,
                'tesla_id': vehicle['id'],
                'tesla_vehicle_id': vehicle['vehicle_id'],
                'vin': vehicle['vin'],
                'vehicle_data': vehicle,
                'display_name': vehicle.get('display_name'),
                'access_type': vehicle.get('access_type'),
                'state': vehicle.get('state'),
                'in_service': vehicle.get('in_service', False),
                'api_version': vehicle.get('api_version'),
                'last_synced_at': datetime.utcnow().isoformat()
            }
            
            # Vérifier si le véhicule existe déjà
            existing = self.supabase.table('vehicles')\
                .select('id')\
                .eq('tesla_account_id', account_id)\
                .eq('tesla_id', vehicle['id'])\
                .limit(1)\
                .execute()
            
            if existing.data and len(existing.data) > 0:
                # Mettre à jour l'entrée existante
                self.supabase.table('vehicles')\
                    .update(vehicle_data)\
                    .eq('id', existing.data[0]['id'])\
                    .execute()
            else:
                # Insérer une nouvelle entrée
                self.supabase.table('vehicles')\
                    .insert(vehicle_data)\
                    .execute()
    
    def get_cached_vehicles(
        self, 
        account_id: str, 
        max_age_minutes: int = 5,
        state: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Récupère les véhicules depuis le cache.
        
        Args:
            account_id: UUID du compte Tesla
            max_age_minutes: Âge maximum du cache en minutes
            state: Filtrer par état (online, offline, asleep)
        
        Returns:
            Liste des véhicules ou None si le cache est expiré
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        
        query = self.supabase.table('vehicles')\
            .select('vehicle_data')\
            .eq('tesla_account_id', account_id)\
            .gte('last_synced_at', cutoff_time.isoformat())
        
        if state:
            query = query.eq('state', state)
        
        result = query.execute()
        
        if result.data and len(result.data) > 0:
            return [item['vehicle_data'] for item in result.data]
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

