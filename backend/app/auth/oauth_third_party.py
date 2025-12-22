from __future__ import annotations
import base64, hashlib, os
import httpx, urllib.parse, secrets
from typing import Optional, Dict, Any
from app.core.settings import settings
from .tp_store import TPStore
from .supabase_store import get_supabase_store

def _generate_pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode("ascii")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge

def build_authorize_url(audience: str | None = None) -> str:
    """
    Construit l'URL /authorize (Tesla Fleet Auth) avec PKCE (S256).
    
    IMPORTANT: Utilise auth.tesla.com pour /authorize (pas fleet-auth).
    L'échange de token utilise fleet-auth.prd.vn.cloud.tesla.com.
    """
    if not (settings.TP_CLIENT_ID and settings.TP_REDIRECT_URI):
        raise RuntimeError("TP_CLIENT_ID/TP_REDIRECT_URI manquants")

    state = secrets.token_urlsafe(16)
    verifier, challenge = _generate_pkce_pair()
    
    # Stocker le verifier PKCE dans Supabase si disponible, sinon en mémoire
    import logging
    logger = logging.getLogger(__name__)
    
    if settings.TOKEN_STORE_TYPE == "supabase":
        try:
            from .supabase_store import get_supabase_store
            
            store = get_supabase_store()
            verifier_key = f"pkce_verifier:{state}"
            # Stocker le verifier avec une expiration de 10 minutes (les codes expirent rapidement)
            store.set(verifier_key, {"verifier": verifier}, ttl=600)
            logger.info(f"✅ PKCE verifier stocké dans Supabase pour state: {state[:8]}... (key: {verifier_key})")
            
            # Vérifier immédiatement que le stockage a fonctionné
            verify_data = store.get(verifier_key)
            if verify_data and verify_data.get("verifier") == verifier:
                logger.info(f"✅ Vérification: PKCE verifier correctement stocké et récupérable")
            else:
                logger.warning(f"⚠️  Vérification échouée: PKCE verifier stocké mais non récupérable immédiatement")
                # Stocker aussi en mémoire comme backup
                TPStore.set_pkce_verifier(state, verifier)
        except Exception as e:
            # Fallback sur mémoire si Supabase échoue
            logger.error(f"❌ Impossible de stocker PKCE verifier dans Supabase: {e}, utilisation du fallback mémoire", exc_info=True)
            TPStore.set_pkce_verifier(state, verifier)
    else:
        logger.info(f"Stockage PKCE verifier en mémoire (TOKEN_STORE_TYPE={settings.TOKEN_STORE_TYPE})")
        TPStore.set_pkce_verifier(state, verifier)

    params = {
        "response_type": "code",
        "client_id": settings.TP_CLIENT_ID,
        "redirect_uri": settings.TP_REDIRECT_URI,
        "scope": settings.TP_SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "prompt": "login",
    }
    # Par défaut, cibler EU pour limiter les redirections 421.
    params["audience"] = audience or settings.tesla_audience_for()

    # Utiliser AUTH_AUTHORIZE_BASE pour /authorize (auth.tesla.com)
    authorize_base = getattr(settings, "AUTH_AUTHORIZE_BASE", None) or settings.TESLA_AUTH_BASE
    return f"{authorize_base}/authorize?{urllib.parse.urlencode(params)}"

async def exchange_code_for_token(code: str, state: Optional[str], issuer: Optional[str] = None) -> Dict[str, Any]:
    """
    Échange le code contre access_token/refresh_token (PKCE).
    
    Args:
        code: Le code d'autorisation reçu du callback
        state: Le state utilisé lors de l'autorisation
        issuer: L'issuer URL fourni par Tesla dans le callback (optionnel, utilise TESLA_AUTH_BASE par défaut)
    """
    if not (settings.TP_CLIENT_ID and settings.TP_REDIRECT_URI):
        raise RuntimeError("TP_CLIENT_ID/TP_REDIRECT_URI manquants")

    # Récupérer le verifier PKCE depuis Supabase si disponible, sinon depuis la mémoire
    code_verifier = None
    import logging
    logger = logging.getLogger(__name__)
    
    if settings.TOKEN_STORE_TYPE == "supabase":
        try:
            from .supabase_store import get_supabase_store
            store = get_supabase_store()
            verifier_key = f"pkce_verifier:{state or ''}"
            logger.info(f"Tentative de récupération du PKCE verifier depuis Supabase pour state: {state[:8] if state else 'None'}...")
            
            verifier_data = store.get(verifier_key)
            logger.info(f"Données récupérées depuis Supabase: {verifier_data is not None}")
            
            if verifier_data:
                code_verifier = verifier_data.get("verifier")
                logger.info(f"PKCE verifier trouvé dans Supabase: {bool(code_verifier)}")
                # Supprimer le verifier après utilisation (one-time use)
                store.delete(verifier_key)
            else:
                logger.warning(f"PKCE verifier non trouvé dans Supabase pour key: {verifier_key}")
                # Essayer aussi depuis la mémoire en fallback
                code_verifier = TPStore.pop_pkce_verifier(state or "")
                if code_verifier:
                    logger.info("PKCE verifier trouvé dans le fallback mémoire")
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du PKCE verifier depuis Supabase: {e}", exc_info=True)
            # Fallback sur mémoire si Supabase échoue
            code_verifier = TPStore.pop_pkce_verifier(state or "")
            if code_verifier:
                logger.info("PKCE verifier trouvé dans le fallback mémoire après erreur Supabase")
    else:
        code_verifier = TPStore.pop_pkce_verifier(state or "")
    
    if not code_verifier:
        # En dernier recours, refuser pour respecter PKCE
        error_msg = (
            f"PKCE verifier introuvable (state expiré ou invalide).\n\n"
            f"State utilisé: {state[:8] if state else 'None'}...\n"
            f"TOKEN_STORE_TYPE: {settings.TOKEN_STORE_TYPE}\n\n"
            f"Le verifier PKCE doit être stocké lors de l'appel à /api/auth/login et récupéré lors du callback.\n"
            f"Vérifiez que:\n"
            f"1. Vous avez bien appelé /api/auth/login avant le callback\n"
            f"2. Le state dans le callback correspond au state généré lors du login\n"
            f"3. Le verifier n'a pas expiré (TTL: 10 minutes)\n"
            f"4. Supabase est accessible et fonctionne correctement"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # IMPORTANT: Pour l'échange de token, on utilise TOUJOURS fleet-auth.prd.vn.cloud.tesla.com
    # L'issuer du callback (auth.tesla.com) est informatif mais ne doit pas être utilisé pour /token
    # L'échange de token DOIT toujours aller vers fleet-auth, peu importe l'issuer du callback
    auth_base = getattr(settings, "AUTH_TOKEN_BASE", None) or settings.TESLA_AUTH_BASE
    
    import logging
    logger = logging.getLogger(__name__)
    if issuer:
        logger.info(f"Issuer du callback ignoré pour /token: {issuer} (utilisation de {auth_base} à la place)")

    data = {
        "grant_type": "authorization_code",
        "client_id": settings.TP_CLIENT_ID,
        "code": code,
        "redirect_uri": settings.TP_REDIRECT_URI,
        "code_verifier": code_verifier,
    }
    if settings.TP_CLIENT_SECRET:
        data["client_secret"] = settings.TP_CLIENT_SECRET

    # Headers pour éviter les blocages CDN/firewall
    # Utiliser un User-Agent qui ressemble à un navigateur pour éviter les blocages
    redirect_uri_base = settings.TP_REDIRECT_URI.split("/api")[0] if settings.TP_REDIRECT_URI else None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    
    # Ajouter Origin et Referer si possible
    if redirect_uri_base:
        headers["Origin"] = redirect_uri_base
        headers["Referer"] = settings.TP_REDIRECT_URI
    
    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS, headers=headers, follow_redirects=True) as client:
        resp = await client.post(f"{auth_base}/token", data=data)
        
        # Gérer les erreurs de manière détaillée
        if resp.status_code == 403:
            error_body = ""
            try:
                error_body = resp.json()
            except:
                error_body = resp.text[:500]
            
            # Vérifier si c'est un blocage Akamai/CDN
            is_akamai_block = "Access Denied" in error_body or "edgesuite.net" in error_body or "<HTML>" in error_body
            
            if is_akamai_block:
                raise RuntimeError(
                    f"Accès bloqué par le CDN/firewall Tesla (403 Forbidden).\n\n"
                    f"L'erreur 'Access Denied' d'Akamai suggère que:\n"
                    f"1. L'IP de votre serveur DigitalOcean est bloquée par Tesla\n"
                    f"2. Il y a un problème de configuration réseau/firewall\n"
                    f"3. Le User-Agent ou les headers ne sont pas acceptés\n\n"
                    f"Issuer utilisé: {auth_base}\n"
                    f"TP_CLIENT_ID utilisé: {settings.TP_CLIENT_ID[:8] if settings.TP_CLIENT_ID else 'Non configuré'}...\n"
                    f"TP_REDIRECT_URI utilisé: {settings.TP_REDIRECT_URI}\n\n"
                    f"Solutions possibles:\n"
                    f"- Contactez Tesla Support pour débloquer votre IP\n"
                    f"- Vérifiez que votre domaine est bien enregistré dans le portail Tesla\n"
                    f"- Essayez depuis une autre IP/réseau\n\n"
                    f"Réponse complète: {error_body[:300]}"
                )
            else:
                raise RuntimeError(
                    f"Tesla a refusé l'échange du code OAuth (403 Forbidden).\n\n"
                    f"Causes possibles:\n"
                    f"1. TP_CLIENT_ID ou TP_CLIENT_SECRET sont incorrects\n"
                    f"2. Le code d'autorisation a expiré (les codes expirent rapidement)\n"
                    f"3. Le code_verifier PKCE ne correspond pas au code_challenge utilisé lors de l'autorisation\n"
                    f"4. Le redirect_uri ne correspond pas exactement à celui configuré dans le portail Tesla\n\n"
                    f"Issuer utilisé: {auth_base}\n"
                    f"TP_CLIENT_ID utilisé: {settings.TP_CLIENT_ID[:8] if settings.TP_CLIENT_ID else 'Non configuré'}...\n"
                    f"TP_REDIRECT_URI utilisé: {settings.TP_REDIRECT_URI}\n\n"
                    f"Réponse Tesla: {error_body}"
                )
        elif resp.status_code == 401:
            error_body = ""
            try:
                error_body = resp.json()
            except:
                error_body = resp.text[:500]
            
            raise RuntimeError(
                f"Authentification OAuth échouée (401 Unauthorized).\n"
                f"Vérifiez que TP_CLIENT_ID et TP_CLIENT_SECRET sont corrects.\n"
                f"Réponse Tesla: {error_body}"
            )
        
        resp.raise_for_status()
        return resp.json()

async def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    # Pour PKCE, pas besoin d'envoyer client_secret
    data = {
        "grant_type": "refresh_token",
        "client_id": settings.TP_CLIENT_ID,
        "refresh_token": refresh_token,
    }
    if settings.TP_CLIENT_SECRET:
        data["client_secret"] = settings.TP_CLIENT_SECRET

    # Utiliser AUTH_TOKEN_BASE pour /token (fleet-auth.prd.vn.cloud.tesla.com)
    token_base = getattr(settings, "AUTH_TOKEN_BASE", None) or settings.TESLA_AUTH_BASE
    
    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
        resp = await client.post(f"{token_base}/token", data=data)
        resp.raise_for_status()
        return resp.json()

async def ensure_user_access_token(user_id: Optional[str] = None, state: Optional[str] = None) -> Optional[str]:
    """
    Retourne un access_token utilisateur valide si disponible,
    sinon tente un refresh avec le refresh_token.
    
    Si user_id est fourni, récupère le token depuis Supabase.
    Si aucun token n'est trouvé pour l'utilisateur, cherche automatiquement
    les tokens temporaires récents (créés dans les 10 dernières minutes) et les lie.
    Si state est fourni, essaie d'abord ce state spécifique.
    Sinon, utilise le store en mémoire (TPStore) pour la rétrocompatibilité.
    """
    # Si user_id est fourni, utiliser Supabase
    if user_id:
        try:
            store = get_supabase_store()
            key = f"user_token:{user_id}"
            token_data = store.get(key)
            
            if token_data:
                access_token = token_data.get("access_token")
                if access_token:
                    return access_token
                
                # Si le token est expiré, essayer de le rafraîchir
                refresh_token = token_data.get("refresh_token")
                if refresh_token:
                    try:
                        new_token = await refresh_access_token(refresh_token)
                        # Stocker le nouveau token dans Supabase
                        expires_in = new_token.get("expires_in", 3600)
                        store.set(key, new_token, ttl=expires_in)
                        return new_token.get("access_token")
                    except Exception:
                        # Si le refresh échoue, retourner None
                        return None
            
            # Si aucun token trouvé pour l'utilisateur, chercher automatiquement
            # les tokens temporaires récents et les lier à l'utilisateur
            temp_token_data = None
            temp_key = None
            
            # D'abord, essayer avec le state fourni si disponible
            if state:
                temp_key = f"temp_token:{state}"
                temp_token_data = store.get(temp_key)
            
            # Si pas de token avec le state fourni, chercher tous les tokens temporaires récents
            if not temp_token_data:
                temp_token_data, temp_key = await _find_recent_temp_token(store)
            
            if temp_token_data and temp_key:
                # Lier le token temporaire à l'utilisateur
                expires_in = temp_token_data.get("expires_in", 3600)
                store.set(key, temp_token_data, ttl=expires_in)
                # Supprimer le token temporaire
                store.delete(temp_key)
                return temp_token_data.get("access_token")
            
            return None
        except Exception:
            # En cas d'erreur Supabase, fallback sur TPStore
            pass
    
    # Fallback sur le store en mémoire (rétrocompatibilité)
    token = TPStore.get_access_token()
    if token:
        return token
    rtk = TPStore.get_refresh_token()
    if not rtk:
        return None
    newtok = await refresh_access_token(rtk)
    TPStore.set_token(newtok)
    return TPStore.get_access_token()


async def _find_recent_temp_token(store) -> tuple[Optional[dict], Optional[str]]:
    """
    Cherche un token temporaire récent (créé dans les 10 dernières minutes).
    Retourne (token_data, key) ou (None, None) si aucun trouvé.
    """
    import time
    from supabase import create_client
    from app.core.settings import settings
    
    try:
        # Utiliser directement Supabase pour chercher les tokens temporaires récents
        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.get_supabase_key_for_admin()
        
        if not supabase_url or not supabase_key:
            return None, None
        
        client = create_client(supabase_url, supabase_key)
        table_name = settings.SUPABASE_TOKENS_TABLE
        
        # Chercher les tokens temporaires créés dans les 10 dernières minutes
        # Les tokens temporaires ont une clé qui commence par "temp_token:"
        import datetime
        ten_minutes_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
        ten_minutes_ago_str = ten_minutes_ago.strftime("%Y-%m-%d %H:%M:%S")
        
        response = client.table(table_name)\
            .select("key, token_data, expires_at, updated_at")\
            .like("key", "temp_token:%")\
            .gte("updated_at", ten_minutes_ago_str)\
            .order("updated_at", desc=True)\
            .limit(1)\
            .execute()
        
        if response.data and len(response.data) > 0:
            token_entry = response.data[0]
            token_data = token_entry.get("token_data")
            if isinstance(token_data, str):
                import json
                token_data = json.loads(token_data)
            return token_data, token_entry.get("key")
        
        return None, None
    except Exception as e:
        # En cas d'erreur, retourner None
        return None, None