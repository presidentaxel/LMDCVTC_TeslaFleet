from __future__ import annotations
import json, time, os
from typing import Optional
import redis

class TokenStore:
    def __init__(self, redis_url: str):
        self._mem: dict[str, str] = {}  # fallback mémoire
        self._use_mem = False
        # Astuce: si REDIS_URL commence par "memory://", on force le mode mémoire
        if redis_url.startswith("memory://"):
            self._use_mem = True
            self.r = None
        else:
            try:
                self.r = redis.from_url(redis_url, decode_responses=True)
                # ping pour vérifier que ça répond, sinon on bascule mémoire
                try:
                    self.r.ping()  # type: ignore[attr-defined]
                except Exception:
                    self._use_mem = True
            except Exception:
                self._use_mem = True
                self.r = None

    def get(self, key: str) -> Optional[dict]:
        try:
            raw = self.r.get(key) if (self.r and not self._use_mem) else self._mem.get(key)
        except Exception:
            raw = self._mem.get(key)
        return json.loads(raw) if raw else None

    def set(self, key: str, token: dict, ttl: int) -> None:
        token = dict(token)
        token["expires_at"] = int(time.time()) + ttl
        payload = json.dumps(token)
        if self.r and not self._use_mem:
            try:
                self.r.setex(key, ttl, payload)
                return
            except Exception:
                # bascule mémoire si erreur
                self._use_mem = True
        self._mem[key] = payload  # pas d’expiration en fallback (ok pour dev)

    def valid(self, token: dict | None) -> bool:
        return bool(token and token.get("access_token") and token.get("expires_at", 0) > time.time()+30)