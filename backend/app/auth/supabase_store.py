"""
Store de tokens utilisant Supabase au lieu de Redis.
Utilise la table 'tokens' dans Supabase pour stocker les tokens OAuth.
"""
from __future__ import annotations
import json
import time
from typing import Optional
from supabase import create_client, Client
from app.core.settings import settings


class SupabaseTokenStore:
    """
    Store de tokens utilisant Supabase PostgreSQL.
    Remplace Redis pour le stockage des tokens OAuth.
    """
    
    def __init__(self, supabase_url: str, supabase_key: str, table_name: str = "tokens"):
        """
        Initialise le store Supabase.
        
        Args:
            supabase_url: URL de votre projet Supabase
            supabase_key: Clé API Supabase (anon key ou service role key)
            table_name: Nom de la table pour stocker les tokens (défaut: "tokens")
        """
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.table_name = table_name
        self._fallback_mem: dict[str, str] = {}  # Fallback en mémoire si Supabase échoue
    
    def get(self, key: str) -> Optional[dict]:
        """
        Récupère un token depuis Supabase.
        
        Args:
            key: Clé du token (ex: "partner_token:eu", "user_token:user123")
            
        Returns:
            Dictionnaire du token ou None si non trouvé/expiré
        """
        try:
            # Récupérer depuis Supabase (tokens non expirés uniquement)
            # expires_at est un TIMESTAMPTZ, on compare avec NOW()
            current_time_iso = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            response = self.supabase.table(self.table_name)\
                .select("token_data, expires_at")\
                .eq("key", key)\
                .gte("expires_at", current_time_iso)\
                .limit(1)\
                .execute()
            
            if response.data and len(response.data) > 0:
                token_data = response.data[0]["token_data"]
                # Si c'est déjà un dict, le retourner tel quel
                if isinstance(token_data, dict):
                    return token_data
                # Sinon, parser le JSON
                return json.loads(token_data) if isinstance(token_data, str) else token_data
            
            # Si pas trouvé dans Supabase, essayer le fallback mémoire
            if key in self._fallback_mem:
                raw = self._fallback_mem[key]
                return json.loads(raw) if isinstance(raw, str) else raw
                
            return None
            
        except Exception as e:
            # En cas d'erreur, utiliser le fallback mémoire
            print(f"⚠️  Erreur Supabase get({key}): {e}, utilisation du fallback mémoire")
            if key in self._fallback_mem:
                raw = self._fallback_mem[key]
                return json.loads(raw) if isinstance(raw, str) else raw
            return None
    
    def set(self, key: str, token: dict, ttl: int) -> None:
        """
        Stocke un token dans Supabase avec expiration.
        
        Args:
            key: Clé du token
            token: Dictionnaire du token
            ttl: Time to live en secondes
        """
        token_copy = dict(token)
        expires_at_ts = int(time.time()) + ttl
        expires_at_iso = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(expires_at_ts))
        
        # Ajouter expires_at au token pour la compatibilité avec valid()
        token_copy["expires_at"] = expires_at_ts
        
        try:
            # Upsert dans Supabase (insert ou update si existe)
            self.supabase.table(self.table_name).upsert({
                "key": key,
                "token_data": token_copy,
                "expires_at": expires_at_iso,
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            }).execute()
            
            # Mettre aussi dans le fallback mémoire
            self._fallback_mem[key] = json.dumps(token_copy)
            
        except Exception as e:
            # En cas d'erreur, utiliser le fallback mémoire
            print(f"⚠️  Erreur Supabase set({key}): {e}, utilisation du fallback mémoire")
            token_copy["expires_at"] = expires_at_ts
            self._fallback_mem[key] = json.dumps(token_copy)
    
    def valid(self, token: dict | None) -> bool:
        """
        Vérifie si un token est valide (non expiré).
        
        Args:
            token: Dictionnaire du token
            
        Returns:
            True si le token est valide, False sinon
        """
        if not token:
            return False
        
        access_token = token.get("access_token")
        expires_at = token.get("expires_at", 0)
        
        # Vérifier que le token existe et n'est pas expiré (avec marge de 30s)
        return bool(access_token and expires_at > time.time() + 30)
    
    def delete(self, key: str) -> None:
        """
        Supprime un token.
        
        Args:
            key: Clé du token à supprimer
        """
        try:
            self.supabase.table(self.table_name).delete().eq("key", key).execute()
        except Exception as e:
            print(f"⚠️  Erreur Supabase delete({key}): {e}")
        
        # Supprimer aussi du fallback mémoire
        self._fallback_mem.pop(key, None)
    
    def cleanup_expired(self) -> None:
        """
        Nettoie les tokens expirés (optionnel, peut être fait par une fonction PostgreSQL).
        """
        try:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            self.supabase.table(self.table_name).delete().lt("expires_at", current_time).execute()
        except Exception as e:
            print(f"⚠️  Erreur Supabase cleanup: {e}")


def get_supabase_store() -> SupabaseTokenStore:
    """
    Factory function pour créer un SupabaseTokenStore depuis les settings.
    """
    supabase_url = getattr(settings, "SUPABASE_URL", None)
    supabase_key = getattr(settings, "SUPABASE_KEY", None)
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "SUPABASE_URL et SUPABASE_KEY doivent être configurés dans les variables d'environnement"
        )
    
    table_name = getattr(settings, "SUPABASE_TOKENS_TABLE", "tokens")
    return SupabaseTokenStore(supabase_url, supabase_key, table_name)

