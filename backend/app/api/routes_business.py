"""Routes API — flotte business (token + véhicules + commandes)."""
from __future__ import annotations

import base64
import json

from fastapi import APIRouter, Depends, HTTPException, Path

from app.auth.business_store import (
    BUSINESS_CACHE_KEY,
    ensure_business_access_token,
    exchange_and_store,
    get_store,
)
from app.auth.business_tokens import BusinessToken
from app.core.settings import settings
from app.schemas.business import (
    BusinessExchangeRequest,
    BusinessExchangeResponse,
    BusinessStatusResponse,
    VehicleCommandRequest,
)
from app.tesla.client import TeslaClient
from app.tesla.command_http import post_vehicle_command
from app.tesla.commands.catalog import COMMANDS, get_command, list_by_category

router = APIRouter(prefix="/business", tags=["business"])

CONSENT_URL = "https://www.tesla.com/teslaaccount/business"
CONSENT_DOCS = "https://developer.tesla.com/docs/fleet-api/authentication/third-party-business-tokens"


@router.get("/consent-guide")
async def consent_guide():
    """Étapes consentement — se fait d'abord sur Tesla for Business, puis code ici."""
    return {
        "title": "Consentement Tesla for Business",
        "note": (
            "Le consentement ne se demande pas via l'API : un admin business "
            "doit l'approuver sur le portail Tesla. Ensuite collez le code ici."
        ),
        "steps": [
            {
                "step": 1,
                "title": "Ouvrir Tesla for Business",
                "action": "open_url",
                "url": CONSENT_URL,
            },
            {
                "step": 2,
                "title": "Account → Consent Management",
                "description": "Menu latéral, section Access Management.",
            },
            {
                "step": 3,
                "title": "Request Consent",
                "description": "Choisir l'app GestionLMDCVTC et l'email admin business.",
            },
            {
                "step": 4,
                "title": "Approuver l'email Tesla",
                "description": "L'admin clique le lien reçu de noreply@tesla.com.",
            },
            {
                "step": 5,
                "title": "Copier l'authorization code",
                "description": "Retour Consent Management → copier le code.",
            },
            {
                "step": 6,
                "title": "Coller le code dans cet outil",
                "action": "exchange_in_app",
            },
        ],
        "docs_url": CONSENT_DOCS,
        "client_id_hint": (settings.TESLA_CLIENT_ID or "")[:8] + "..." if settings.TESLA_CLIENT_ID else None,
    }


def _decode_scopes(token: str) -> str | None:
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        scp = payload.get("scp")
        if isinstance(scp, list):
            return " ".join(scp)
        return str(scp) if scp else None
    except Exception:
        return None


@router.get("/status", response_model=BusinessStatusResponse)
async def business_status():
    store = get_store()
    cached = store.get(BUSINESS_CACHE_KEY)
    active = store.valid(cached)
    preview = None
    if active and cached:
        preview = cached["access_token"][:12] + "..."
    return BusinessStatusResponse(
        token_active=active,
        access_token_preview=preview,
        expires_in=cached.get("expires_in") if cached else None,
        scope=cached.get("scope") if cached else None,
        client_id_set=bool(settings.TESLA_CLIENT_ID or settings.TP_CLIENT_ID),
        client_secret_set=bool(settings.TESLA_CLIENT_SECRET or settings.TP_CLIENT_SECRET),
        audience=settings.tesla_audience_for(),
        consent_steps_completed=active,
    )


@router.post("/exchange", response_model=BusinessExchangeResponse)
async def business_exchange(body: BusinessExchangeRequest):
    try:
        token: BusinessToken = await exchange_and_store(body.auth_code.strip())
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return BusinessExchangeResponse(
        success=True,
        expires_in=token.expires_in,
        scope=token.scope,
        access_token_preview=token.access_token[:12] + "...",
    )


@router.delete("/token")
async def business_revoke_token():
    store = get_store()
    if hasattr(store, "delete"):
        store.delete(BUSINESS_CACHE_KEY)
    return {"ok": True, "message": "Token business supprimé du cache local."}


@router.get("/vehicles")
async def business_vehicles(page: int = 1, page_size: int = 50):
    try:
        access = await ensure_business_access_token()
    except RuntimeError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    client = TeslaClient(access_token=access)
    try:
        return await client.vehicles_list(page=page, page_size=page_size)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur liste véhicules: {e}") from e


@router.get("/commands/catalog")
async def commands_catalog():
    return {"categories": list_by_category(), "total": len(COMMANDS)}


@router.post("/vehicles/{vehicle_ref}/commands/{command_name}")
async def run_business_command(
    vehicle_ref: str = Path(..., description="ID ou VIN du véhicule"),
    command_name: str = Path(...),
    payload: VehicleCommandRequest | None = None,
):
    cmd = get_command(command_name)
    if not cmd and command_name != "wake_up":
        raise HTTPException(status_code=404, detail=f"Commande inconnue: {command_name}")
    try:
        access = await ensure_business_access_token()
    except RuntimeError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    body = (payload.body if payload else None) or {}
    try:
        return await post_vehicle_command(access, vehicle_ref, command_name, body)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
