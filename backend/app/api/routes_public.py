from fastapi import APIRouter, HTTPException, Response
from pathlib import Path
from app.core.settings import settings
import logging
import re

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health():
    return {"status": "ok"}


# Tesla n'accepte que les clés EC prime256v1 ; la clé publique PEM fait ~180-200 octets.
# Une clé RSA 2048 ou un fichier incorrect (ex. clé privée) dépasse cette taille → "too large".
MAX_PUBLIC_KEY_PEM_BYTES = 1024

def _normalize_public_key_pem(content: bytes) -> bytes:
    """Retourne uniquement le premier bloc PEM PUBLIC KEY (sans BOM/espaces en trop)."""
    text = content.decode("utf-8", errors="replace").strip()
    match = re.search(
        r"-----BEGIN PUBLIC KEY-----[\r\n]+[A-Za-z0-9+/=\r\n]+-----END PUBLIC KEY-----",
        text,
        re.DOTALL,
    )
    if match:
        return match.group(0).encode("utf-8")
    return content.strip()

def _validate_and_return_pem(content: bytes) -> Response:
    """Vérifie la taille (Tesla rejette si trop gros) et renvoie la réponse."""
    normalized = _normalize_public_key_pem(content)
    if len(normalized) > MAX_PUBLIC_KEY_PEM_BYTES:
        logger.error(
            "Clé publique trop grande (%s octets). Tesla exige une clé EC prime256v1. "
            "Si vous avez une clé RSA, régénérez avec: python scripts/generate_tesla_keys.py",
            len(normalized),
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "La clé publique servie est trop volumineuse pour Tesla (limite ~1 Ko). "
                "L'API Fleet exige une clé EC prime256v1, pas RSA. "
                "Régénérez les clés avec: python scripts/generate_tesla_keys.py"
            ),
        )
    if not normalized.startswith(b"-----BEGIN PUBLIC KEY-----"):
        raise HTTPException(
            status_code=500,
            detail="Le fichier ne contient pas une clé publique PEM valide (BEGIN PUBLIC KEY).",
        )
    return Response(
        content=normalized,
        media_type="application/x-pem-file",
        headers={"Content-Disposition": 'attachment; filename="com.tesla.3p.public-key.pem"'},
    )

@router.get("/.well-known/appspecific/com.tesla.3p.public-key.pem")
async def get_public_key():
    """
    Endpoint pour servir la clé publique Tesla (EC prime256v1 uniquement).
    Requis par Tesla pour l'enregistrement partenaire. La clé est générée depuis la clé privée si besoin.
    """
    # Chemins possibles pour la clé publique
    possible_paths = [
        Path("/app/app/keys/public/public_key.pem"),  # Docker volume
        Path("./app/keys/public/public_key.pem"),      # Dev local
        Path("app/keys/public/public_key.pem"),        # Alternative
        Path("/app/keys/public/public_key.pem"),       # Alternative Docker
    ]
    
    # Si PRIVATE_KEY_PATH est défini, déduire le chemin de la clé publique
    private_key_path = None
    if hasattr(settings, "PRIVATE_KEY_PATH") and settings.PRIVATE_KEY_PATH:
        private_key_path = Path(settings.PRIVATE_KEY_PATH)
        if "private" in str(private_key_path):
            public_key_path = private_key_path.parent.parent / "public" / "public_key.pem"
        else:
            public_key_path = private_key_path.parent / "public_key.pem"
        possible_paths.insert(0, public_key_path)
    
    # Servir le fichier de clé publique existant (en validant taille et format)
    for key_path in possible_paths:
        if key_path.exists() and key_path.is_file():
            try:
                content = key_path.read_bytes()
            except Exception as e:
                logger.warning(f"Impossible de lire {key_path}: {e}")
                continue
            return _validate_and_return_pem(content)
    
    # Essayer de générer la clé publique depuis la clé privée
    private_key_paths_to_try = [
        *( [private_key_path] if private_key_path else [] ),
        Path("/app/app/keys/private/private_key.pem"),
        Path("./app/keys/private/private_key.pem"),
        Path("app/keys/private/private_key.pem"),
        Path("/app/keys/private/private_key.pem"),
        Path("/run/secrets/tesla_private_key.pem"),
    ]
    
    for priv_path in private_key_paths_to_try:
        if not priv_path or not priv_path.exists() or not priv_path.is_file():
            continue
        logger.info(f"Clé privée trouvée à: {priv_path}, génération de la clé publique...")
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend
            
            with open(priv_path, "rb") as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend(),
                )
            public_key = private_key.public_key()
            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            return _validate_and_return_pem(public_key_pem)
        except Exception as e:
            logger.warning(f"Impossible de générer la clé publique depuis {priv_path}: {e}")
            continue
    
    error_detail = (
        "Clé publique non trouvée et impossible de la générer depuis la clé privée.\n\n"
        f"PRIVATE_KEY_PATH configuré: {getattr(settings, 'PRIVATE_KEY_PATH', 'Non configuré')}\n\n"
        "Chemins vérifiés pour la clé privée:\n"
    )
    for priv_path in private_key_paths_to_try:
        if priv_path:
            error_detail += f"  {'✓' if priv_path.exists() else '✗'} {priv_path}\n"
    error_detail += (
        "\nPour résoudre : configurez PRIVATE_KEY_PATH ou placez la clé publique dans "
        "app/keys/public/public_key.pem. Tesla exige une clé EC prime256v1 (générer avec scripts/generate_tesla_keys.py)."
    )
    raise HTTPException(status_code=404, detail=error_detail)