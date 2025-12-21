"""
Factory pour créer le bon type de store selon la configuration.
Permet de basculer entre Redis, Supabase ou mémoire.
"""
from typing import Union
from app.core.settings import settings
from app.auth.token_store import TokenStore
from app.auth.supabase_store import SupabaseTokenStore, get_supabase_store


def get_token_store() -> Union[TokenStore, SupabaseTokenStore]:
    """
    Crée le store de tokens approprié selon la configuration.
    
    Priorité:
    1. TOKEN_STORE_TYPE="supabase" → SupabaseTokenStore
    2. TOKEN_STORE_TYPE="redis" → TokenStore (Redis)
    3. Sinon → TokenStore (mémoire)
    """
    store_type = getattr(settings, "TOKEN_STORE_TYPE", "memory").lower()
    
    if store_type == "supabase":
        try:
            return get_supabase_store()
        except (ValueError, Exception) as e:
            print(f"⚠️  Impossible d'utiliser Supabase: {e}, bascule vers mémoire")
            return TokenStore("memory://dev")
    
    elif store_type == "redis":
        return TokenStore(settings.REDIS_URL)
    
    else:  # memory ou par défaut
        return TokenStore("memory://dev")

