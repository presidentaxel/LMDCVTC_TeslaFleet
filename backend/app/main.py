from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.settings import settings
from app.api import api_router

def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)
    
    # Configuration CORS - Parse les origines depuis les settings
    cors_origins = [
        origin.strip()
        for origin in settings.CORS_ORIGINS.split(",")
        if origin.strip()
    ]
    
    # En développement, accepter aussi les IPs réseau (172.x.x.x, 192.x.x.x, 10.x.x.x)
    if settings.ENV == "dev":
        cors_origins.append("*")  # En dev, accepter toutes les origines pour faciliter le développement
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if settings.ENV != "dev" else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Prometheus metrics
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
    
    app.include_router(api_router, prefix=settings.API_PREFIX)
    return app

app = create_app()