from __future__ import annotations
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field, HttpUrl, validator

AllowedMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
AudienceRegion = Literal["eu", "na"]
TokenType = Literal["user", "partner"]


class FleetProxyRequest(BaseModel):
    method: AllowedMethod = Field(description="Méthode HTTP à utiliser pour l'appel Fleet API.")
    path: str = Field(description="Chemin Fleet API commençant par /api/...")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Query string optionnelle.")
    json: Optional[Dict[str, Any]] = Field(default=None, description="Payload JSON pour POST/PUT/PATCH.")
    region: AudienceRegion = Field(default="eu", description="Région d'audience Fleet.")
    token_type: TokenType = Field(default="user", description="Choisir le token utilisateur (OAuth) ou partenaire (client_credentials).")

    @validator("path")
    def ensure_leading_slash(cls, v: str) -> str:
        if not v.startswith("/"):
            raise ValueError("Le chemin doit commencer par '/'.")
        return v


class FleetProxyResponse(BaseModel):
    status_code: int
    headers: Dict[str, str]
    body: Any

