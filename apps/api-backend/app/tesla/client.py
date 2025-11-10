from __future__ import annotations
import httpx
from typing import Any, Dict, Optional
from app.core.settings import settings

class TeslaClient:
    def __init__(self, base_url: Optional[str]=None, access_token: Optional[str]=None):
        self.base_url = (base_url or settings.TESLA_AUDIENCE_EU).rstrip("/")
        self.access_token = access_token

    def _headers(self) -> Dict[str,str]:
        h = {"Content-Type": "application/json"}
        if self.access_token:
            h["Authorization"] = f"Bearer {self.access_token}"
        return h

    async def _do(self, method: str, url: str, *, json: Any = None, params: dict | None = None) -> httpx.Response:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS, http2=True) as client:
            resp = await client.request(method, url, headers=self._headers(), json=json, params=params)
            return resp

    async def request(self, method: str, path: str, *, json: Any = None, params: dict | None = None, allow_error: bool = False) -> httpx.Response:
        url = f"{self.base_url}{path}"
        resp = await self._do(method, url, json=json, params=params)

        # Fallback 421 (mauvaise région)
        if resp.status_code == 421:
            loc = resp.headers.get("Location") or resp.headers.get("location")
            if loc:
                resp2 = await self._do(method, loc, json=json, params=params)
                if resp2.is_error and not allow_error:
                    raise httpx.HTTPStatusError(f"{resp2.status_code} {resp2.reason_phrase}: {await self._safe_text(resp2)}", request=None, response=resp2)
                return resp2
            alt = settings.TESLA_AUDIENCE_NA if self.base_url.startswith(settings.TESLA_AUDIENCE_EU) else settings.TESLA_AUDIENCE_EU
            resp2 = await self._do(method, f"{alt.rstrip('/')}{path}", json=json, params=params)
            if resp2.is_error and not allow_error:
                raise httpx.HTTPStatusError(f"{resp2.status_code} {resp2.reason_phrase}: {await self._safe_text(resp2)}", request=None, response=resp2)
            return resp2

        if resp.is_error and not allow_error:
            raise httpx.HTTPStatusError(f"{resp.status_code} {resp.reason_phrase}: {await self._safe_text(resp)}", request=None, response=resp)
        return resp

    async def _safe_text(self, resp: httpx.Response) -> str:
        try:
            t = resp.text
            return t[:500]
        except Exception:
            return "<no body>"

    async def status(self) -> dict:
        resp = await self.request("GET", "/status")
        # /status peut renvoyer du texte
        try:
            return resp.json()
        except Exception:
            return {"raw": (resp.text[:200] if resp.text else "")}

    async def vehicles_list(self, page: int = 1, page_size: int = 50) -> dict:
        path = settings.TESLA_VEHICLES_PATH
        params = {"page": page, "page_size": page_size}
        resp = await self.request("GET", path, params=params)
        return resp.json()

    async def partner_fleet_telemetry_errors(self) -> dict:
        resp = await self.request("GET", "/api/1/partner_accounts/fleet_telemetry_errors")
        return resp.json()
    
    async def wake_up(self, vehicle_id: str) -> dict:
        path = settings.TESLA_CMD_WAKE.format(id=vehicle_id)
        resp = await self.request("POST", path)
        return resp.json()

    async def door_lock(self, vehicle_id: str) -> dict:
        path = settings.TESLA_CMD_LOCK.format(id=vehicle_id)
        resp = await self.request("POST", path)
        return resp.json()

    async def door_unlock(self, vehicle_id: str) -> dict:
        path = settings.TESLA_CMD_UNLOCK.format(id=vehicle_id)
        resp = await self.request("POST", path)
        return resp.json()

    async def charge_start(self, vehicle_id: str) -> dict:
        path = settings.TESLA_CMD_CHARGE_START.format(id=vehicle_id)
        resp = await self.request("POST", path)
        return resp.json()

    async def charge_stop(self, vehicle_id: str) -> dict:
        path = settings.TESLA_CMD_CHARGE_STOP.format(id=vehicle_id)
        resp = await self.request("POST", path)
        return resp.json()
    
    async def partner_register(self, domain: str, public_key_url: str | None = None) -> dict:
        body = {"domain": domain}
        if public_key_url:
            body["public_key_url"] = public_key_url
        resp = await self.request("POST", "/api/1/partner_accounts", json=body)
        return resp.json() if resp.content else {"ok": True}

    async def partner_public_key(self, domain: str) -> dict:
        # Vérif post-enregistrement
        resp = await self.request("GET", f"/api/1/partner_accounts/public_key", params={"domain": domain})
        return resp.json()
