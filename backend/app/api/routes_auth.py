from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request, Depends, status, Query
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.core.settings import settings
from app.auth.oauth_third_party import build_authorize_url, exchange_code_for_token
from app.auth.tp_store import TPStore
from app.auth.supabase_auth import require_supabase_user
from app.auth.supabase_auth import oauth2_scheme
from supabase import create_client
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login")
async def auth_login():
    url = build_authorize_url()  # audience EU par défaut
    return RedirectResponse(url, status_code=307)

@router.get("/callback")
async def auth_callback(request: Request):
    """
    Callback OAuth. Échange le code contre un token et redirige vers le frontend.
    Stocke le token dans Supabase avec une clé temporaire basée sur le state.
    """
    from fastapi.responses import RedirectResponse
    from app.auth.supabase_store import get_supabase_store
    
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")
    issuer = request.query_params.get("issuer")  # Issuer fourni par Tesla dans le callback
    
    # URL du frontend (configurée via env ou settings)
    frontend_url = settings.FRONTEND_URL
    
    if error:
        # Rediriger vers le frontend avec l'erreur
        return RedirectResponse(
            url=f"{frontend_url}/auth?error={error}",
            status_code=307
        )
    
    if not code:
        return RedirectResponse(
            url=f"{frontend_url}/auth?error=missing_code",
            status_code=307
        )

    try:
        # Utiliser l'issuer fourni par Tesla si disponible
        token = await exchange_code_for_token(code, state, issuer=issuer)
        
        # Stocker dans TPStore pour la rétrocompatibilité
        TPStore.set_token(token)
        
        # Stocker aussi dans Supabase avec une clé temporaire basée sur le state
        # Le token sera lié à l'utilisateur lors de la première requête authentifiée
        if state and settings.TOKEN_STORE_TYPE == "supabase":
            try:
                store = get_supabase_store()
                temp_key = f"temp_token:{state}"
                expires_in = token.get("expires_in", 3600)
                store.set(temp_key, token, ttl=expires_in)
            except Exception as e:
                logger.warning(f"Impossible de stocker le token temporaire dans Supabase: {e}")
        
        # Rediriger vers le frontend avec succès
        return RedirectResponse(
            url=f"{frontend_url}/auth?success=true&state={state}",
            status_code=307
        )
    except RuntimeError as e:
        # RuntimeError contient déjà les détails de l'erreur
        error_msg = str(e).replace(" ", "%20").replace("\n", "%0A")
        logger.error(f"Erreur lors de l'échange du code OAuth: {e}")
        return RedirectResponse(
            url=f"{frontend_url}/auth?error={error_msg}",
            status_code=307
        )
    except httpx.HTTPStatusError as e:
        error_body = ""
        try:
            error_body = e.response.json() if e.response else ""
        except:
            error_body = str(e.response.text[:200]) if e.response else str(e)
        
        error_msg = f"Erreur HTTP {e.response.status_code if e.response else 'unknown'}: {error_body}".replace(" ", "%20").replace("\n", "%0A")
        logger.error(f"Erreur HTTP lors de l'échange du code OAuth: {error_msg}")
        return RedirectResponse(
            url=f"{frontend_url}/auth?error={error_msg}",
            status_code=307
        )
    except Exception as e:
        # Rediriger vers le frontend avec l'erreur
        error_msg = str(e).replace(" ", "%20").replace("\n", "%0A")
        logger.error(f"Erreur inattendue lors de l'échange du code OAuth: {e}", exc_info=True)
        return RedirectResponse(
            url=f"{frontend_url}/auth?error={error_msg}",
            status_code=307
        )
    
@router.get("/authorize-url")
async def auth_authorize_url():
    return {"url": build_authorize_url()}

@router.get("/debug")
async def auth_debug(token: str | None = Depends(oauth2_scheme)):
    """
    Endpoint de debug pour vérifier la configuration et l'état des tokens.
    Accessible sans authentification, mais si un token Supabase est fourni,
    vérifie aussi le token Tesla associé.
    """
    from app.auth.oauth_third_party import ensure_user_access_token
    from app.auth.supabase_store import get_supabase_store
    from app.auth.supabase_auth import get_user_id_from_token
    
    # Essayer de récupérer les infos utilisateur si un token est fourni
    user_info = None
    user_id = None
    if token:
        try:
            # Vérifier le token Supabase sans lever d'exception si invalide
            from app.auth.supabase_auth import require_supabase_user
            user_info = await require_supabase_user(token)
            user_id = user_info.get("user_id") if user_info else None
        except Exception:
            # Token invalide ou expiré, continuer sans info utilisateur
            pass
    
    # Si user_id disponible, essayer de récupérer le token Tesla
    user_token = None
    if user_id:
        try:
            user_token = await ensure_user_access_token(user_id=user_id)
        except Exception:
            pass
    
    # Vérifier le token dans Supabase si user_id est disponible
    token_in_supabase = None
    if user_id and settings.TOKEN_STORE_TYPE == "supabase":
        try:
            store = get_supabase_store()
            key = f"user_token:{user_id}"
            token_data = store.get(key)
            token_in_supabase = {
                "found": token_data is not None,
                "has_access_token": bool(token_data.get("access_token") if token_data else False),
                "has_refresh_token": bool(token_data.get("refresh_token") if token_data else False),
            }
        except Exception as e:
            token_in_supabase = {"error": str(e)}
    
    # Tester les méthodes de récupération de clés
    try:
        anon_key = settings.get_supabase_key_for_auth()
        service_key = settings.get_supabase_key_for_admin()
    except Exception as e:
        anon_key = f"ERROR: {e}"
        service_key = f"ERROR: {e}"
    
    # Tester la connexion Supabase
    supabase_test = {}
    if settings.SUPABASE_URL and anon_key and not isinstance(anon_key, str):
        try:
            test_client = create_client(settings.SUPABASE_URL, anon_key)
            # Essayer de récupérer les settings (test de connexion)
            supabase_test["connection_ok"] = True
            supabase_test["message"] = "Connexion Supabase OK"
        except Exception as e:
            supabase_test["connection_ok"] = False
            supabase_test["error"] = str(e)
    else:
        supabase_test["connection_ok"] = False
        supabase_test["message"] = "Configuration Supabase incomplète"
    
    result = {
        "auth_base": settings.TESLA_AUTH_BASE,
        "tp_redirect_uri": settings.TP_REDIRECT_URI,
        "tp_client_id_set": bool(settings.TP_CLIENT_ID),
        "tp_client_secret_set": bool(settings.TP_CLIENT_SECRET),
        "scopes": settings.TP_SCOPES,
        "user_token_active": bool(user_token),
        "user_token_preview": (user_token[:12] + "..." if user_token else None),
        "supabase_url": settings.SUPABASE_URL,
        "supabase_anon_key_set": bool(settings.SUPABASE_ANON_KEY),
        "supabase_service_key_set": bool(settings.SUPABASE_SERVICE_ROLE_KEY),
        "supabase_key_set": bool(settings.SUPABASE_KEY),
        "supabase_anon_key_preview": (settings.SUPABASE_ANON_KEY[:20] + "..." if settings.SUPABASE_ANON_KEY else None),
        "supabase_service_key_preview": (settings.SUPABASE_SERVICE_ROLE_KEY[:20] + "..." if settings.SUPABASE_SERVICE_ROLE_KEY else None),
        "supabase_key_preview": (settings.SUPABASE_KEY[:20] + "..." if settings.SUPABASE_KEY else None),
        "token_store_type": settings.TOKEN_STORE_TYPE,
        "key_used_for_auth": "ANON" if settings.SUPABASE_ANON_KEY else ("SERVICE" if settings.SUPABASE_SERVICE_ROLE_KEY else "GENERIC"),
        "get_supabase_key_for_auth_result": bool(anon_key) if isinstance(anon_key, str) else bool(anon_key),
        "get_supabase_key_for_admin_result": bool(service_key) if isinstance(service_key, str) else bool(service_key),
        "supabase_test": supabase_test,
        "token_provided": bool(token),
        "user_authenticated": bool(user_info),
    }
    
    if user_id:
        result["user_id"] = user_id
        result["token_in_supabase"] = token_in_supabase
        if not user_token:
            result["warning"] = "Token Tesla non trouvé. Avez-vous complété le flux OAuth via /api/auth/login et lié le token via /api/auth/link-token ?"
    elif token:
        result["warning"] = "Token Supabase invalide ou expiré. Obtenez un nouveau token via /api/auth/supabase/token"
    
    return result


@router.post("/link-token")
async def link_tesla_token(
    state: str = Query(..., description="State du callback OAuth pour lier le token Tesla"),
    user_info: dict = Depends(require_supabase_user),
):
    """
    Lie un token Tesla temporaire (basé sur le state du callback OAuth) à l'utilisateur authentifié.
    Cette route doit être appelée après le callback OAuth pour associer le token Tesla à l'utilisateur Supabase.
    """
    from app.auth.supabase_store import get_supabase_store
    
    user_id = user_info.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID utilisateur introuvable",
        )
    
    try:
        store = get_supabase_store()
        temp_key = f"temp_token:{state}"
        temp_token_data = store.get(temp_key)
        
        if not temp_token_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Token temporaire introuvable pour le state: {state}. Le token a peut-être expiré ou le state est invalide.",
            )
        
        # Lier le token temporaire à l'utilisateur
        user_key = f"user_token:{user_id}"
        expires_in = temp_token_data.get("expires_in", 3600)
        store.set(user_key, temp_token_data, ttl=expires_in)
        
        # Supprimer le token temporaire
        store.delete(temp_key)
        
        return {
            "success": True,
            "message": "Token Tesla lié à votre compte avec succès",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la liaison du token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la liaison du token: {str(e)}",
        )


@router.post("/supabase/token")
async def supabase_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Flow password pour récupérer un JWT Supabase directement depuis Swagger.
    Utilise SUPABASE_ANON_KEY de préférence, sinon SUPABASE_KEY.
    """
    try:
        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.get_supabase_key_for_auth()
        
        logger.info(f"Tentative de login Supabase pour: {form_data.username}")
        logger.debug(f"SUPABASE_URL: {supabase_url}")
        logger.debug(f"SUPABASE_ANON_KEY défini: {bool(settings.SUPABASE_ANON_KEY)}")
        logger.debug(f"SUPABASE_KEY défini: {bool(settings.SUPABASE_KEY)}")
        logger.debug(f"Clé utilisée pour auth: {'ANON' if settings.SUPABASE_ANON_KEY else ('GENERIC' if settings.SUPABASE_KEY else 'AUCUNE')}")
        
        if not supabase_url:
            logger.error("SUPABASE_URL manquant")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SUPABASE_URL manquant dans la configuration",
            )
        
        if not supabase_key:
            logger.error("Aucune clé Supabase configurée pour l'authentification")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Clé Supabase manquante. Configurez SUPABASE_ANON_KEY (recommandé) ou SUPABASE_KEY pour l'authentification.",
            )

        # Utiliser le SDK Supabase pour l'authentification (plus fiable que les appels HTTP directs)
        try:
            logger.debug(f"Création du client Supabase avec URL: {supabase_url}, clé preview: {supabase_key[:20]}...")
            supabase_client = create_client(supabase_url, supabase_key)
            logger.debug(f"Tentative de connexion pour email: {form_data.username}")
            auth_response = supabase_client.auth.sign_in_with_password({
                "email": form_data.username,
                "password": form_data.password,
            })
            
            if not auth_response or not auth_response.session:
                logger.error("Supabase n'a pas retourné de session")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Identifiants Supabase invalides ou email non confirmé",
                )
            
            access_token = auth_response.session.access_token
            if not access_token:
                logger.error("Pas de access_token dans la session Supabase")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Supabase n'a pas retourné de token d'accès",
                )
            
        except Exception as exc:
            error_msg = str(exc)
            error_type = type(exc).__name__
            logger.error(f"Erreur authentification Supabase ({error_type}): {error_msg}", exc_info=True)
            
            # Essayer de extraire un message d'erreur plus utile
            if "Invalid login credentials" in error_msg or "invalid_credentials" in error_msg.lower():
                detail_msg = (
                    "Identifiants Supabase invalides. "
                    "Vérifiez que:\n"
                    "1. L'email est correct\n"
                    "2. Le mot de passe est correct\n"
                    "3. L'utilisateur existe dans Supabase (Dashboard > Authentication > Users)\n"
                    "4. L'email est confirmé (vérifiez dans Supabase Dashboard)"
                )
            elif "Email not confirmed" in error_msg or "email_not_confirmed" in error_msg.lower():
                detail_msg = (
                    "Email non confirmé. "
                    "Vérifiez votre boîte mail pour confirmer votre compte, "
                    "ou désactivez la confirmation d'email dans Supabase Dashboard > Authentication > Settings"
                )
            else:
                detail_msg = f"Erreur authentification Supabase ({error_type}): {error_msg}"
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail_msg,
            )

        logger.info(f"Login réussi pour: {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException:
        # Re-raise les HTTPException telles quelles
        raise
    except Exception as e:
        # Capturer toutes les autres exceptions non gérées
        logger.error(f"Erreur inattendue dans supabase_token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}",
        )