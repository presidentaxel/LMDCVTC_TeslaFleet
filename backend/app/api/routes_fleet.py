"""
Endpoints FLEET - Endpoints généraux et partenaire.
Ce fichier contient les endpoints qui ne nécessitent pas de cache ou qui sont spécifiques au mode partenaire.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
import httpx
from app.core.settings import settings
from app.auth.store_factory import get_token_store
from app.auth.token_store import TokenStore
from app.auth.supabase_store import SupabaseTokenStore
from typing import Union
from app.auth.partner_tokens import get_partner_token_cached
from app.tesla.client import TeslaClient

router = APIRouter(
    prefix="/fleet",
    tags=["fleet"],
)

def get_store() -> Union[TokenStore, SupabaseTokenStore]:
    """Retourne le store de tokens configuré (Redis, Supabase ou mémoire)"""
    return get_token_store()

def user_client_or_401(token: str | None):
    if not token:
        raise HTTPException(status_code=401, detail="No user token. Call /api/auth/login first.")
    return TeslaClient(access_token=token)

@router.get("/status")
async def fleet_status(store: TokenStore = Depends(get_store)):
    """
    Statut de l'API Fleet (utilise le token partenaire).
    """
    try:
        try:
            token = await get_partner_token_cached(store)
        except RuntimeError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Impossible d'obtenir le token partenaire: {str(e)}"
            )
        
        client = TeslaClient(access_token=token)
        return await client.status()
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Fleet status error: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fleet status error: {e}")

# ============================================================================
# ENDPOINTS PARTENAIRE (M2M)
# ============================================================================

@router.get("/partner/telemetry-errors")
async def partner_telemetry_errors(store: TokenStore = Depends(get_store)):
    """
    Récupère les erreurs de télémétrie de la flotte partenaire.
    Note: Cet endpoint nécessite un token partenaire (client_credentials) ET que l'application
    ait les permissions partenaire activées dans le portail Tesla Developer.
    
    Si vous obtenez 403 "Unauthorized missing scopes", cela signifie que :
    1. Votre token partenaire n'a pas les scopes nécessaires
    2. Votre application n'a pas les permissions partenaire dans le portail Tesla Developer
    3. Vous devez utiliser un token utilisateur (third-party OAuth) au lieu d'un token partenaire pour cet endpoint
    """
    try:
        try:
            token = await get_partner_token_cached(store)  # partner token requis
        except RuntimeError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Impossible d'obtenir le token partenaire: {str(e)}"
            )
        
        client = TeslaClient(access_token=token)
        
        # Utiliser un timeout plus long pour cet endpoint qui peut être lent
        try:
            return await client.partner_fleet_telemetry_errors()
        except httpx.TimeoutException as e:
            raise HTTPException(
                status_code=504,
                detail=f"Timeout lors de l'appel à l'API Tesla (timeout: {settings.HTTP_TIMEOUT_SECONDS}s). Réessayez plus tard."
            )
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        error_detail = f"Partner telemetry error: {e}"
        # Si 403, donner plus de contexte
        if e.response and e.response.status_code == 403:
            error_detail += (
                "\n\nErreur 403 (missing scopes): Le token partenaire n'a pas les scopes nécessaires. "
                "À faire: (1) Vérifier que PARTNER_SCOPES est défini (ex: openid vehicle_device_data vehicle_cmds vehicle_charging_cmds) et redémarrer pour obtenir un nouveau token. "
                "(2) Dans le portail Tesla Developer (developer.tesla.com), activer les produits/permissions partenaire pour votre app (ex. Fleet Telemetry). "
                "Puis appeler GET /api/fleet/partner/token-debug pour vérifier les scopes du token."
            )
        elif e.response and e.response.status_code == 401:
            error_detail += " - Vérifie que l'application a les permissions partenaire dans le portail Tesla Developer"
        raise HTTPException(status_code=502, detail=error_detail)
    except httpx.TimeoutException as e:
        raise HTTPException(
            status_code=504,
            detail=f"Timeout lors de l'appel à l'API Tesla: {str(e)}"
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur inattendue: {str(e)}")

def _decode_jwt_scopes(access_token: str) -> str | None:
    """Decode JWT payload (sans vérification) et retourne le claim scp pour debug."""
    try:
        import base64
        import json
        parts = access_token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1]
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        scp = payload.get("scp")
        if scp is None:
            return None
        if isinstance(scp, list):
            return " ".join(scp)
        return str(scp)
    except Exception:
        return None


# DEBUG: te permet de vérifier ton token partenaire
@router.get("/partner/token-debug")
async def partner_token_debug(
    store: TokenStore = Depends(get_store),
    refresh: bool = Query(False, description="Si true, ignore le cache et demande un nouveau token à Tesla"),
):
    """
    Debug: Affiche les infos du token partenaire (scopes, audience, etc.).
    Utilisez ?refresh=1 pour forcer un nouveau token (utile après avoir ajouté PARTNER_SCOPES).
    """
    from app.auth.partner_tokens import fetch_partner_token, PARTNER_CACHE_KEY

    requested_scopes = getattr(settings, "PARTNER_SCOPES", None) or None

    # Vérifier qu'au moins une paire de credentials est configurée
    has_tesla = bool(settings.TESLA_CLIENT_ID and settings.TESLA_CLIENT_SECRET)
    has_tp = bool(settings.TP_CLIENT_ID and settings.TP_CLIENT_SECRET)
    if not has_tesla and not has_tp:
        return {
            "error": "TESLA_CLIENT_ID/SECRET ou TP_CLIENT_ID/SECRET manquants",
            "tesla_client_id_set": bool(settings.TESLA_CLIENT_ID),
            "tesla_client_secret_set": bool(settings.TESLA_CLIENT_SECRET),
            "auth_base": settings.TESLA_AUTH_BASE,
            "audience": settings.tesla_audience_for(),
        }

    try:
        # Utiliser le cache sauf si ?refresh=1
        cached_token = None if refresh else store.get(PARTNER_CACHE_KEY)
        if cached_token and store.valid(cached_token):
            access_token = cached_token.get("access_token", "")
            scopes_granted = cached_token.get("scope")
            scopes_in_jwt = _decode_jwt_scopes(access_token) if access_token else None
            out = {
                "access_token_preview": access_token[:12] + "..." if access_token else "",
                "audience": settings.tesla_audience_for(),
                "auth_base": settings.TESLA_AUTH_BASE,
                "scopes": scopes_granted,
                "scopes_requested": requested_scopes,
                "scopes_in_jwt": scopes_in_jwt,
                "expires_in": cached_token.get("expires_in"),
                "token_type": cached_token.get("token_type"),
                "source": "cache",
            }
            if scopes_granted is None and scopes_in_jwt is None:
                out["hint"] = "scopes null = token en cache obtenu sans PARTNER_SCOPES, ou Tesla ne renvoie pas ce champ. Utilisez ?refresh=1 pour forcer un nouveau token."
            return out
        
        # Sinon, essayer de fetch un nouveau token avec TESLA_CLIENT_ID d'abord
        result = {
            "tesla_client_id_set": bool(settings.TESLA_CLIENT_ID),
            "tesla_client_secret_set": bool(settings.TESLA_CLIENT_SECRET),
            "tp_client_id_set": bool(settings.TP_CLIENT_ID),
            "tp_client_secret_set": bool(settings.TP_CLIENT_SECRET),
            "auth_base": settings.TESLA_AUTH_BASE,
            "audience": settings.tesla_audience_for(),
            "expected_client_id": "cacad6ff-48dd-4e8f-b521-8180d0865b94",
        }
        
        result["scopes_requested"] = requested_scopes

        # Essayer avec TESLA_CLIENT_ID d'abord
        if settings.TESLA_CLIENT_ID and settings.TESLA_CLIENT_SECRET:
            try:
                token_obj = await fetch_partner_token(use_tp_credentials=False)
                result.update({
                    "access_token_preview": token_obj.access_token[:12] + "...",
                    "scopes": token_obj.scope,
                    "scopes_in_jwt": _decode_jwt_scopes(token_obj.access_token),
                    "expires_in": token_obj.expires_in,
                    "token_type": token_obj.token_type,
                    "source": "fresh",
                    "credentials_used": "TESLA_CLIENT_ID",
                    "success": True,
                })
                return result
            except RuntimeError as e:
                result["tesla_error"] = str(e)
                result["tesla_success"] = False
        
        # Si TESLA_CLIENT_ID échoue, essayer avec TP_CLIENT_ID
        if settings.TP_CLIENT_ID and settings.TP_CLIENT_SECRET:
            try:
                token_obj = await fetch_partner_token(use_tp_credentials=True)
                result.update({
                    "access_token_preview": token_obj.access_token[:12] + "...",
                    "scopes": token_obj.scope,
                    "scopes_in_jwt": _decode_jwt_scopes(token_obj.access_token),
                    "expires_in": token_obj.expires_in,
                    "token_type": token_obj.token_type,
                    "source": "fresh",
                    "credentials_used": "TP_CLIENT_ID",
                    "success": True,
                })
                return result
            except RuntimeError as e:
                result["tp_error"] = str(e)
                result["tp_success"] = False
        
        # Si les deux ont échoué
        result["error"] = "Impossible d'obtenir un token partenaire avec aucun des credentials configurés"
        result["success"] = False
        return result
    except RuntimeError as e:
        # RuntimeError contient déjà les détails de l'erreur
        return {
            "error": str(e),
            "tesla_client_id_set": bool(settings.TESLA_CLIENT_ID),
            "tesla_client_secret_set": bool(settings.TESLA_CLIENT_SECRET),
            "tp_client_id_set": bool(settings.TP_CLIENT_ID),
            "tp_client_secret_set": bool(settings.TP_CLIENT_SECRET),
            "auth_base": settings.TESLA_AUTH_BASE,
            "audience": settings.tesla_audience_for(),
            "expected_client_id": "cacad6ff-48dd-4e8f-b521-8180d0865b94",
        }
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "tesla_client_id_set": bool(settings.TESLA_CLIENT_ID),
            "tesla_client_secret_set": bool(settings.TESLA_CLIENT_SECRET),
            "tp_client_id_set": bool(settings.TP_CLIENT_ID),
            "tp_client_secret_set": bool(settings.TP_CLIENT_SECRET),
            "auth_base": settings.TESLA_AUTH_BASE,
            "audience": settings.tesla_audience_for(),
            "expected_client_id": "cacad6ff-48dd-4e8f-b521-8180d0865b94",
        }

@router.post("/partner/register")
async def partner_register(store: TokenStore = Depends(get_store)):
    """
    Enregistre l'application dans la région courante (résout le 412).
    Nécessite un partner token (client-credentials).
    
    Note: Le domaine doit être un vrai domaine (pas localhost) pour être accepté par Tesla.
    En développement, utilisez un domaine de test ou ngrok.
    
    IMPORTANT: Si vous obtenez une erreur 403 lors de l'obtention du token partenaire,
    essayez d'utiliser TP_CLIENT_ID/TP_CLIENT_SECRET au lieu de TESLA_CLIENT_ID/TESLA_CLIENT_SECRET
    si vous utilisez le même CLIENT_ID pour les deux types de tokens.
    """
    from app.auth.partner_tokens import fetch_partner_token
    
    try:
        # Essayer d'obtenir le token partenaire depuis le cache d'abord
        token = None
        try:
            token = await get_partner_token_cached(store)
        except RuntimeError as e:
            # Si le cache échoue, essayer avec TP credentials (au cas où vous utilisez le même CLIENT_ID)
            error_msg = str(e)
            if "403" in error_msg or "Forbidden" in error_msg:
                # Essayer avec TP credentials si disponibles
                if settings.TP_CLIENT_ID and settings.TP_CLIENT_SECRET:
                    try:
                        token_obj = await fetch_partner_token(use_tp_credentials=True)
                        # Mettre en cache
                        ttl = max(60, int(token_obj.expires_in) - 60)
                        store.set("tesla:partner_token:eu", token_obj.model_dump(), ttl=ttl)
                        token = token_obj.access_token
                    except Exception as e2:
                        raise HTTPException(
                            status_code=502,
                            detail=(
                                f"Impossible d'obtenir le token partenaire avec TESLA_CLIENT_ID: {error_msg}\n\n"
                                f"Tentative avec TP_CLIENT_ID également échouée: {str(e2)}\n\n"
                                f"Vérifiez que:\n"
                                f"1. Vos credentials sont corrects (CLIENT_ID devrait être: cacad6ff-48dd-4e8f-b521-8180d0865b94)\n"
                                f"2. Le CLIENT_SECRET correspond bien à ce CLIENT_ID\n"
                                f"3. Les permissions partenaire sont activées dans le portail Tesla Developer"
                            )
                        )
                else:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Impossible d'obtenir le token partenaire: {error_msg}"
                    )
            else:
                raise HTTPException(
                    status_code=502,
                    detail=f"Impossible d'obtenir le token partenaire: {error_msg}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Erreur lors de la récupération du token partenaire: {str(e)}"
            )
        
        if not token:
            raise HTTPException(
                status_code=502,
                detail="Impossible d'obtenir un token partenaire valide"
            )
        
        client = TeslaClient(access_token=token)

        domain = (getattr(settings, "APP_DOMAIN", None) or "").strip()
        if not domain:
            raise HTTPException(
                status_code=400, 
                detail="APP_DOMAIN manquant dans la configuration. Configurez APP_DOMAIN avec un vrai domaine (pas localhost)."
            )
        
        # Nettoyer le domaine : enlever http://, https://, et convertir en minuscules
        domain = domain.lower()
        if domain.startswith("http://"):
            domain = domain[7:]
        elif domain.startswith("https://"):
            domain = domain[8:]
        # Enlever le port si présent (localhost:8000 -> localhost)
        if ":" in domain:
            domain = domain.split(":")[0]
        
        # Vérifier que ce n'est pas localhost
        if domain == "localhost" or domain.startswith("127.") or domain.startswith("192.168.") or domain.startswith("10."):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Le domaine '{domain}' n'est pas accepté par Tesla. "
                    "Utilisez un vrai domaine (ex: example.com) ou un service comme ngrok pour le développement. "
                    "Tesla n'accepte pas localhost, 127.0.0.1 ou les adresses IP privées."
                )
            )

        pk_url = getattr(settings, "PUBLIC_KEY_URL", None)
        
        # Appeler l'API Tesla avec gestion d'erreurs améliorée
        try:
            data = await client.partner_register(domain=domain, public_key_url=pk_url)
            return {"ok": True, "register": data, "domain": domain}
        except httpx.TimeoutException as e:
            raise HTTPException(
                status_code=504,
                detail=(
                    f"Timeout lors de l'enregistrement du domaine '{domain}' avec Tesla. "
                    f"L'API Tesla a pris trop de temps à répondre. Réessayez plus tard.\n"
                    f"Erreur: {str(e)}"
                )
            )
        except httpx.ConnectError as e:
            raise HTTPException(
                status_code=502,
                detail=(
                    f"Impossible de se connecter à l'API Tesla. "
                    f"Vérifiez votre connexion internet et que l'API Tesla est accessible.\n"
                    f"Erreur: {str(e)}"
                )
            )
        except httpx.HTTPStatusError as e:
            error_detail = f"Erreur lors de l'enregistrement du domaine '{domain}': {e}"
            
            # Extraire le message d'erreur de Tesla si disponible
            try:
                if e.response:
                    error_body = e.response.json()
                    error_detail += f"\n\nRéponse Tesla: {error_body}"
                    
                    # Messages spécifiques selon le code d'erreur
                    if e.response.status_code == 400:
                        if "Invalid domain" in str(error_body):
                            error_detail += "\n\nNote: Tesla n'accepte pas localhost. Utilisez un vrai domaine ou ngrok."
                    elif e.response.status_code == 401:
                        error_detail += "\n\nErreur 401: Le token partenaire n'est pas valide ou a expiré."
                    elif e.response.status_code == 403:
                        error_detail += "\n\nErreur 403: Vous n'avez pas les permissions nécessaires pour enregistrer un domaine."
                    elif e.response.status_code == 409:
                        error_detail += "\n\nErreur 409: Le domaine est déjà enregistré. C'est normal si vous avez déjà enregistré ce domaine."
            except:
                pass
            
            raise HTTPException(status_code=502, detail=error_detail)
    except HTTPException:
        raise
    except Exception as e:
        # Capturer toutes les autres exceptions pour éviter les 502 génériques
        import traceback
        error_trace = traceback.format_exc()
        raise HTTPException(
            status_code=500,
            detail=(
                f"Erreur inattendue lors de l'enregistrement partenaire: {str(e)}\n\n"
                f"Type d'erreur: {type(e).__name__}\n"
                f"Traceback: {error_trace[:500]}"
            )
        )

@router.get("/partner/public-key")
async def partner_public_key(store: TokenStore = Depends(get_store)):
    """
    Récupère la clé publique enregistrée pour le domaine partenaire.
    Note: Cet endpoint nécessite des scopes que le token partenaire (client_credentials)
    n'a généralement pas. Utilise le token partenaire uniquement.
    """
    try:
        try:
            token = await get_partner_token_cached(store)
        except RuntimeError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Impossible d'obtenir le token partenaire: {str(e)}"
            )
        
        client = TeslaClient(access_token=token)
        domain = (getattr(settings, "APP_DOMAIN", None) or "").strip()
        if not domain:
            raise HTTPException(status_code=400, detail="APP_DOMAIN manquant dans la configuration")
        
        # Nettoyer le domaine
        domain = domain.lower()
        if domain.startswith("http://"):
            domain = domain[7:]
        elif domain.startswith("https://"):
            domain = domain[8:]
        if ":" in domain:
            domain = domain.split(":")[0]
        
        try:
            return await client.partner_public_key(domain)
        except httpx.TimeoutException as e:
            raise HTTPException(
                status_code=504,
                detail=f"Timeout lors de l'appel à l'API Tesla (timeout: {settings.HTTP_TIMEOUT_SECONDS}s). Réessayez plus tard."
            )
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        error_detail = f"Partner public_key error: {e}"
        if e.response:
            try:
                error_body = e.response.json()
                error_detail += f"\n\nRéponse Tesla: {error_body}"
            except:
                pass
        raise HTTPException(status_code=502, detail=error_detail)
    except httpx.TimeoutException as e:
        raise HTTPException(
            status_code=504,
            detail=f"Timeout lors de l'appel à l'API Tesla: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur inattendue: {str(e)}"
        )