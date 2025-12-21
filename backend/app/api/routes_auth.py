from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse
from app.core.settings import settings
from app.auth.oauth_third_party import build_authorize_url, exchange_code_for_token
from app.auth.tp_store import TPStore

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login")
async def auth_login():
    url = build_authorize_url()  # audience EU par défaut
    return RedirectResponse(url, status_code=307)

@router.get("/callback")
async def auth_callback(request: Request):
    """
    Callback OAuth. Échange le code contre un token et redirige vers le frontend.
    """
    from fastapi.responses import RedirectResponse
    
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")
    
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
        token = await exchange_code_for_token(code, state)
        TPStore.set_token(token)
        # Rediriger vers le frontend avec succès
        return RedirectResponse(
            url=f"{frontend_url}/auth?success=true",
            status_code=307
        )
    except Exception as e:
        # Rediriger vers le frontend avec l'erreur
        error_msg = str(e).replace(" ", "%20")
        return RedirectResponse(
            url=f"{frontend_url}/auth?error={error_msg}",
            status_code=307
        )
    
@router.get("/authorize-url")
async def auth_authorize_url():
    return {"url": build_authorize_url()}

@router.get("/debug")
async def auth_debug():
    from app.auth.oauth_third_party import ensure_user_access_token
    user_token = await ensure_user_access_token()
    return {
        "auth_base": settings.TESLA_AUTH_BASE,
        "tp_redirect_uri": settings.TP_REDIRECT_URI,
        "tp_client_id_set": bool(settings.TP_CLIENT_ID),
        "tp_client_secret_set": bool(settings.TP_CLIENT_SECRET),
        "scopes": settings.TP_SCOPES,
        "user_token_active": bool(user_token),
        "user_token_preview": (user_token[:12] + "..." if user_token else None),
    }