from fastapi import APIRouter
from .routes_public import router as public_router
from .routes_fleet import router as fleet_router
from .routes_auth import router as auth_router

api_router = APIRouter()
api_router.include_router(public_router, prefix="", tags=["public"])
api_router.include_router(auth_router, prefix="", tags=["auth"])
api_router.include_router(fleet_router, prefix="", tags=["fleet"])