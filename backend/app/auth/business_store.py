"""Cache du token business (mémoire, Redis ou Supabase)."""
from __future__ import annotations

from typing import Union

from app.auth.business_tokens import BUSINESS_CACHE_KEY, BusinessToken, fetch_business_token
from app.auth.store_factory import get_token_store
from app.auth.supabase_store import SupabaseTokenStore
from app.auth.token_store import TokenStore
from app.core.settings import settings

Store = Union[TokenStore, SupabaseTokenStore]


def get_store() -> Store:
    return get_token_store()


def save_token(store: Store, token: BusinessToken) -> None:
    ttl = max(60, int(token.expires_in) - 60)
    store.set(BUSINESS_CACHE_KEY, token.model_dump(), ttl=ttl)


async def exchange_and_store(auth_code: str, store: Store | None = None) -> BusinessToken:
    store = store or get_store()
    token = await fetch_business_token(auth_code)
    save_token(store, token)
    return token


async def get_cached_access_token(store: Store | None = None) -> str | None:
    store = store or get_store()
    cached = store.get(BUSINESS_CACHE_KEY)
    if store.valid(cached):
        return cached["access_token"]
    return None


async def ensure_business_access_token(
    store: Store | None = None,
    *,
    auth_code: str | None = None,
) -> str:
    store = store or get_store()
    token = await get_cached_access_token(store)
    if token:
        return token
    code = (auth_code or settings.TESLA_BUSINESS_AUTH_CODE or "").strip()
    if not code:
        raise RuntimeError(
            "Token business absent. Complétez le consentement Tesla for Business "
            "puis échangez le code via POST /api/business/exchange."
        )
    fresh = await exchange_and_store(code, store)
    return fresh.access_token
