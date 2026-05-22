"""Exécution des commandes véhicule via REST Fleet API."""
from __future__ import annotations

from typing import Any

import httpx

from app.core.settings import settings
from app.tesla.client import TeslaClient


def command_path(vehicle_ref: str, command_name: str) -> str:
    if command_name == "wake_up":
        return f"/api/1/vehicles/{vehicle_ref}/wake_up"
    return f"/api/1/vehicles/{vehicle_ref}/command/{command_name}"


async def post_vehicle_command(
    access_token: str,
    vehicle_ref: str,
    command_name: str,
    body: dict[str, Any] | None = None,
    *,
    region: str | None = None,
) -> dict[str, Any]:
    client = TeslaClient(
        base_url=settings.tesla_audience_for(region),
        access_token=access_token,
    )
    resp = await client.request(
        "POST",
        command_path(vehicle_ref, command_name),
        json=body or {},
        allow_error=True,
    )
    try:
        payload: Any = resp.json()
    except ValueError:
        payload = {"raw": resp.text[:500]}
    return {
        "status_code": resp.status_code,
        "success": resp.is_success,
        "body": payload,
    }
