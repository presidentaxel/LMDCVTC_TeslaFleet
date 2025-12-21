from __future__ import annotations
import time
from typing import Optional, Dict, Any

class TPStore:
    """
    Store en mémoire (dev) pour le token utilisateur issu de l'OAuth authorization_code.
    En prod: remplace par DB/Redis chiffré et multi-utilisateurs.
    """
    _token: Optional[Dict[str, Any]] = None
    _pkce_by_state: Dict[str, str] = {}

    @classmethod
    def set_token(cls, token: Dict[str, Any]) -> None:
        # On calcule un expires_at
        exp = int(time.time()) + int(token.get("expires_in", 3600))
        token = dict(token)
        token["expires_at"] = exp
        cls._token = token

    @classmethod
    def get_access_token(cls) -> Optional[str]:
        if not cls._token:
            return None
        if cls._token.get("expires_at", 0) <= time.time() + 30:
            return None
        return cls._token.get("access_token")

    @classmethod
    def get_refresh_token(cls) -> Optional[str]:
        if not cls._token:
            return None
        return cls._token.get("refresh_token")

    # ---- PKCE (state -> code_verifier) ----
    @classmethod
    def set_pkce_verifier(cls, state: str, code_verifier: str) -> None:
        cls._pkce_by_state[state] = code_verifier

    @classmethod
    def pop_pkce_verifier(cls, state: str) -> Optional[str]:
        if not state:
            return None
        return cls._pkce_by_state.pop(state, None)