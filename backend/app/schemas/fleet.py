from pydantic import BaseModel


class PartnerStatusResponse(BaseModel):
    token_active: bool
    token_mode: str = "partner"
    access_token_preview: str | None = None
    expires_in: int | None = None
    scope: str | None = None
    client_id_set: bool
    client_secret_set: bool
    audience: str
    note: str | None = None


class FleetAccessStatusResponse(BaseModel):
    """Statut agrégé : partenaire M2M (prioritaire) ou business (consent)."""

    token_active: bool
    active_mode: str | None = None  # "partner" | "business" | None
    partner_token_active: bool
    business_token_active: bool
    access_token_preview: str | None = None
    expires_in: int | None = None
    scope: str | None = None
    client_id_set: bool
    client_secret_set: bool
    audience: str
