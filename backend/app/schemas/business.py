from pydantic import BaseModel, Field


class BusinessExchangeRequest(BaseModel):
    auth_code: str = Field(..., min_length=8, description="Code depuis Tesla for Business > Consent Management")


class BusinessExchangeResponse(BaseModel):
    success: bool
    expires_in: int
    scope: str | None = None
    access_token_preview: str


class BusinessStatusResponse(BaseModel):
    token_active: bool
    access_token_preview: str | None = None
    expires_in: int | None = None
    scope: str | None = None
    client_id_set: bool
    client_secret_set: bool
    audience: str
    consent_steps_completed: bool


class VehicleCommandRequest(BaseModel):
    body: dict | None = None
