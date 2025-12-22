from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path

# Déterminer quel fichier .env charger selon l'environnement
# Stratégie : charger .env d'abord, puis .env.dev ou .env.prod selon ENV
# ENV peut venir de l'environnement système ou être défini dans .env

# Chercher les fichiers .env dans plusieurs emplacements possibles
# 1. Répertoire courant (où le serveur est lancé)
# 2. Répertoire backend/ (relatif au répertoire courant)
# 3. Répertoire backend/ (depuis le répertoire de ce fichier)
base_paths = [
    Path("."),  # Répertoire courant
    Path("backend"),  # backend/ depuis le répertoire courant
    Path(__file__).parent.parent.parent,  # backend/ depuis ce fichier (backend/app/core/settings.py)
]

def find_env_file(filename: str) -> str | None:
    """Trouve un fichier .env dans les répertoires possibles."""
    for base in base_paths:
        env_path = base / filename
        if env_path.exists():
            return str(env_path)
    return None

env_files = []
# Charger .env d'abord s'il existe
env_file = find_env_file(".env")
if env_file:
    env_files.append(env_file)

# Vérifier ENV depuis l'environnement système (priorité)
env = os.getenv("ENV")
if not env and env_file:
    # Si pas dans l'env système, essayer de lire depuis .env
    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("ENV=") and not line.startswith("#"):
                    env = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    except Exception:
        pass

env = env or "dev"

# Ajouter le fichier spécifique selon l'environnement (les valeurs écrasent .env)
if env == "dev":
    dev_env_file = find_env_file(".env.dev")
    if dev_env_file:
        env_files.append(dev_env_file)
elif env == "prod":
    prod_env_file = find_env_file(".env.prod")
    if prod_env_file:
        env_files.append(prod_env_file)

class Settings(BaseSettings):
    # Charge les fichiers dans l'ordre : .env puis .env.dev/.env.prod
    # Les valeurs du dernier fichier écrasent les précédentes
    model_config = SettingsConfigDict(env_file=env_files, extra="ignore")

    APP_NAME: str = "tesla-fleet-api"
    API_PREFIX: str = "/api"
    ENV: str = "dev"

    # Tesla Auth URLs - IMPORTANT: Séparer authorize et token
    # Authorize (login + consent) : https://auth.tesla.com/oauth2/v3/authorize
    # Token (exchange code) : https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token
    TESLA_AUTH_BASE: str = "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3"  # Deprecated, utiliser AUTH_AUTHORIZE_BASE et AUTH_TOKEN_BASE
    AUTH_AUTHORIZE_BASE: str = "https://auth.tesla.com/oauth2/v3"  # Pour /authorize (login + consent)
    AUTH_TOKEN_BASE: str = "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3"  # Pour /token (exchange code)
    
    TESLA_AUDIENCE_EU: str = "https://fleet-api.prd.eu.vn.cloud.tesla.com"
    TESLA_AUDIENCE_NA: str = "https://fleet-api.prd.na.vn.cloud.tesla.com"
    TESLA_REGION: str = "eu"

    TESLA_CLIENT_ID: str | None = None          # partner (m2m)
    TESLA_CLIENT_SECRET: str | None = None      # partner

    TESLA_VEHICLES_PATH: str = "/api/1/vehicles"

    # Third-party (authorization_code)
    TP_CLIENT_ID: str | None = None
    TP_CLIENT_SECRET: str | None = None
    TP_REDIRECT_URI: str | None = None
    TP_SCOPES: str = "openid offline_access vehicle_device_data vehicle_cmds vehicle_charging_cmds"

    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/postgres"
    REDIS_URL: str = "memory://dev"
    
    # Supabase Configuration (alternative à Redis)
    SUPABASE_URL: str | None = None
    
    # Clés Supabase - Le code choisira automatiquement la bonne clé selon le contexte :
    # - Authentification utilisateur (login) : utilise SUPABASE_ANON_KEY (recommandé) ou SUPABASE_KEY
    # - Opérations admin (stockage tokens, vérification) : utilise SUPABASE_SERVICE_ROLE_KEY (recommandé) ou SUPABASE_KEY
    # 
    # Configuration recommandée :
    #   SUPABASE_ANON_KEY=<anon-key>          # Pour /api/auth/supabase/token (login)
    #   SUPABASE_SERVICE_ROLE_KEY=<service>   # Pour stockage tokens et vérification bearer tokens
    #
    # Configuration minimale (fallback) :
    #   SUPABASE_KEY=<any-key>                # Utilisée partout si les clés spécifiques ne sont pas définies
    SUPABASE_KEY: str | None = None  # Clé générique (fallback si ANON_KEY ou SERVICE_ROLE_KEY absentes)
    SUPABASE_ANON_KEY: str | None = None  # Anon Key (pour authentification utilisateur - recommandé)
    SUPABASE_SERVICE_ROLE_KEY: str | None = None  # Service Role Key (pour opérations admin - recommandé)
    
    SUPABASE_TOKENS_TABLE: str = "tokens"  # Nom de la table pour les tokens
    
    # Choix du store: "redis", "supabase", ou "memory"
    TOKEN_STORE_TYPE: str = "memory"  # Par défaut: mémoire (dev), changez en "supabase" pour utiliser Supabase
    
    def get_supabase_anon_key(self) -> str | None:
        """Retourne la clé anon Supabase (pour auth utilisateur)."""
        return self.SUPABASE_ANON_KEY or self.SUPABASE_KEY
    
    def get_supabase_service_key(self) -> str | None:
        """Retourne la clé service role Supabase (pour opérations admin)."""
        return self.SUPABASE_SERVICE_ROLE_KEY or self.SUPABASE_KEY
    
    def get_supabase_key_for_auth(self) -> str | None:
        """Retourne la clé appropriée pour l'authentification (anon de préférence)."""
        return self.get_supabase_anon_key()
    
    def get_supabase_key_for_admin(self) -> str | None:
        """Retourne la clé appropriée pour les opérations admin (service role de préférence)."""
        return self.get_supabase_service_key()

    APP_DOMAIN: str | None = None
    PUBLIC_KEY_URL: str | None = None

    PUBLIC_KEY_URL: str = "https://localhost/.well-known/appspecific/com.tesla.3p.public-key.pem"
    PRIVATE_KEY_PATH: str = "/run/secrets/tesla_private_key.pem"
    
    # Frontend URL pour les redirections OAuth
    FRONTEND_URL: str = "http://localhost:5173"
    
    # CORS - Liste des origines autorisées (séparées par des virgules)
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    TESLA_CMD_WAKE: str = "/api/1/vehicles/{id}/wake_up"
    TESLA_CMD_LOCK: str = "/api/1/vehicles/{id}/command/door_lock"
    TESLA_CMD_UNLOCK: str = "/api/1/vehicles/{id}/command/door_unlock"
    TESLA_CMD_CHARGE_START: str = "/api/1/vehicles/{id}/command/charge_start"
    TESLA_CMD_CHARGE_STOP: str = "/api/1/vehicles/{id}/command/charge_stop"

    HTTP_TIMEOUT_SECONDS: int = 15
    RETRY_MAX: int = 3

    def tesla_audience_for(self, region: str | None = None) -> str:
        """
        Retourne l'audience Fleet adaptée à la région souhaitée.
        - "eu" pour Europe/Middle East/Africa
        - "na" pour North America/Asia Pacific
        Toute autre valeur retombe sur EU par défaut.
        """
        reg = (region or self.TESLA_REGION or "").strip().lower()

        if reg in {"na", "northamerica", "northamericaasiapacific", "north_america", "northamericaapac"}:
            return self.TESLA_AUDIENCE_NA

        # Valeurs acceptées pour l'Europe
        if reg in {"eu", "emea", "europe", "europe-middle-east-africa"}:
            return self.TESLA_AUDIENCE_EU

        # Fallback sûr : EU
        return self.TESLA_AUDIENCE_EU

# Logger les fichiers chargés au démarrage
if env_files:
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Chargement des fichiers d'environnement: {env_files}")
    logger.info(f"ENV détecté: {env}")
else:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("Aucun fichier .env trouvé, utilisation des variables d'environnement système uniquement")

settings = Settings()