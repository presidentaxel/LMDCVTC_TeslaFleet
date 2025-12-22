from __future__ import annotations
import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.settings import settings

# Swagger affichera un prompt user/pass via ce flow, puis ajoutera le Bearer automatiquement
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/supabase/token", auto_error=False)


def get_user_id_from_token(token: str) -> str | None:
    """
    Décode le JWT Supabase pour extraire l'ID utilisateur (sub).
    Retourne None si le token ne peut pas être décodé.
    """
    try:
        # Décoder sans vérification (on fait confiance à Supabase pour la vérification)
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get("sub")
    except Exception:
        return None


async def require_supabase_user(token: str | None = Depends(oauth2_scheme)):
    """
    Vérifie le bearer token Supabase via l'endpoint /auth/v1/user.
    Utilise SUPABASE_SERVICE_ROLE_KEY de préférence (pour bypass RLS), sinon SUPABASE_ANON_KEY ou SUPABASE_KEY.
    Retourne un dict avec 'user' (profil) et 'user_id' (ID utilisateur).
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header manquant. Utilisez le flow /api/auth/supabase/token pour obtenir un token.",
        )

    supabase_url = settings.SUPABASE_URL
    supabase_key = settings.get_supabase_key_for_admin()  # Service role pour vérifier les tokens
    
    if not supabase_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL manquant dans la configuration",
        )
    
    if not supabase_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clé Supabase manquante. Configurez SUPABASE_SERVICE_ROLE_KEY (recommandé) ou SUPABASE_KEY pour la vérification des tokens.",
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": supabase_key,
    }
    user_url = supabase_url.rstrip("/") + "/auth/v1/user"

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(user_url, headers=headers)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Vérification Supabase indisponible: {exc}",
        )

    if resp.status_code != 200:
        try:
            error_data = resp.json()
            error_msg = error_data.get("error_description") or error_data.get("error") or resp.text
        except:
            error_msg = resp.text[:200]
        
        detail_msg = f"Token Supabase invalide ou expiré ({resp.status_code}): {error_msg}"
        if resp.status_code == 401:
            detail_msg += " - Le token a peut-être expiré, reconnectez-vous via /api/auth/supabase/token"
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail_msg,
        )

    user_data = resp.json()
    # Extraire l'ID utilisateur depuis le token JWT ou depuis user_data
    user_id = get_user_id_from_token(token) or user_data.get("id") or user_data.get("sub")
    
    return {
        "user": user_data,
        "user_id": user_id,
        "token": token,  # Garder le token pour usage downstream si besoin
    }

