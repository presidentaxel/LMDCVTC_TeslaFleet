from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "tesla-fleet-api"
    API_PREFIX: str = "/api"
    ENV: str = "dev"

    TESLA_AUTH_BASE: str = "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3"
    TESLA_AUDIENCE_EU: str = "https://fleet-api.prd.eu.vn.cloud.tesla.com"
    TESLA_AUDIENCE_NA: str = "https://fleet-api.prd.na.vn.cloud.tesla.com"

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

settings = Settings()