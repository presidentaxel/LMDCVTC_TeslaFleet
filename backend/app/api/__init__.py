from fastapi import APIRouter
from .routes_public import router as public_router
from .routes_fleet import router as fleet_router
from .routes_fleet_sync import router as fleet_sync_router
from .routes_fleet_direct import router as fleet_direct_router
from .routes_fleet_supabase import router as fleet_supabase_router
from .routes_auth import router as auth_router

api_router = APIRouter()
# Router public sans prefix pour que /.well-known soit accessible directement
api_router.include_router(public_router, prefix="", tags=["public"])
api_router.include_router(auth_router, prefix="", tags=["auth"])
api_router.include_router(fleet_router, prefix="", tags=["fleet"])
api_router.include_router(fleet_sync_router, prefix="", tags=["fleet-sync"])
api_router.include_router(fleet_direct_router, prefix="", tags=["fleet-direct"])
api_router.include_router(fleet_supabase_router, prefix="", tags=["fleet-supabase"])