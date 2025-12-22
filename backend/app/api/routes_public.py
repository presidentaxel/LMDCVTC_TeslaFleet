from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pathlib import Path
from app.core.settings import settings
import os

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/.well-known/appspecific/com.tesla.3p.public-key.pem")
async def get_public_key():
    """
    Endpoint pour servir la clé publique Tesla.
    Cet endpoint est requis par Tesla pour l'enregistrement partenaire.
    La clé publique est générée automatiquement depuis la clé privée si nécessaire.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Chercher la clé publique dans différents emplacements possibles
    possible_paths = [
        Path("/app/app/keys/public/public_key.pem"),  # Docker volume
        Path("./app/keys/public/public_key.pem"),      # Dev local
        Path("app/keys/public/public_key.pem"),        # Alternative
        Path("/app/keys/public/public_key.pem"),       # Alternative Docker
    ]
    
    # Si PRIVATE_KEY_PATH est défini, essayer de déduire le chemin de la clé publique
    private_key_path = None
    if hasattr(settings, "PRIVATE_KEY_PATH") and settings.PRIVATE_KEY_PATH:
        private_key_path = Path(settings.PRIVATE_KEY_PATH)
        logger.info(f"PRIVATE_KEY_PATH configuré: {private_key_path}")
        
        # Si c'est une clé privée, chercher la clé publique dans le même répertoire ou dans public/
        if "private" in str(private_key_path):
            public_key_path = private_key_path.parent.parent / "public" / "public_key.pem"
            possible_paths.insert(0, public_key_path)
            logger.info(f"Chemin déduit pour clé publique: {public_key_path}")
        else:
            # Si le chemin contient déjà le nom du fichier, essayer de le remplacer
            public_key_path = private_key_path.parent / "public_key.pem"
            possible_paths.insert(0, public_key_path)
            logger.info(f"Chemin alternatif pour clé publique: {public_key_path}")
    
    # Chercher le fichier de clé publique existant
    for key_path in possible_paths:
        if key_path.exists() and key_path.is_file():
            logger.info(f"Clé publique trouvée à: {key_path}")
            return FileResponse(
                path=str(key_path),
                media_type="application/x-pem-file",
                filename="public_key.pem"
            )
    
    # Si aucune clé publique n'est trouvée, essayer de la générer depuis la clé privée
    if private_key_path:
        # Essayer plusieurs chemins possibles pour la clé privée
        private_key_paths_to_try = [
            private_key_path,
            Path("/app/app/keys/private/private_key.pem"),
            Path("./app/keys/private/private_key.pem"),
            Path("app/keys/private/private_key.pem"),
            Path("/app/keys/private/private_key.pem"),
            Path("/run/secrets/tesla_private_key.pem"),  # Docker secrets
        ]
        
        for priv_path in private_key_paths_to_try:
            if priv_path.exists() and priv_path.is_file():
                logger.info(f"Clé privée trouvée à: {priv_path}, génération de la clé publique...")
                try:
                    # Extraire la clé publique depuis la clé privée
                    from cryptography.hazmat.primitives import serialization
                    from cryptography.hazmat.backends import default_backend
                    
                    with open(priv_path, "rb") as f:
                        private_key = serialization.load_pem_private_key(
                            f.read(),
                            password=None,
                            backend=default_backend()
                        )
                    
                    public_key = private_key.public_key()
                    public_key_pem = public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    )
                    
                    logger.info("Clé publique générée avec succès depuis la clé privée")
                    return Response(
                        content=public_key_pem,
                        media_type="application/x-pem-file",
                        headers={"Content-Disposition": 'attachment; filename="public_key.pem"'}
                    )
                except Exception as e:
                    logger.error(f"Erreur lors de la génération de la clé publique depuis {priv_path}: {str(e)}")
                    # Continuer à essayer les autres chemins
                    continue
    
    # Si on arrive ici, aucune clé n'a été trouvée
    error_detail = (
        "Clé publique non trouvée et impossible de la générer depuis la clé privée.\n\n"
        f"PRIVATE_KEY_PATH configuré: {settings.PRIVATE_KEY_PATH if hasattr(settings, 'PRIVATE_KEY_PATH') else 'Non configuré'}\n\n"
        "Chemins vérifiés pour la clé privée:\n"
    )
    for priv_path in private_key_paths_to_try if private_key_path else []:
        exists = "✓" if priv_path.exists() else "✗"
        error_detail += f"  {exists} {priv_path}\n"
    
    error_detail += (
        "\nPour résoudre ce problème:\n"
        "1. Configurez PRIVATE_KEY_PATH dans vos variables d'environnement\n"
        "2. Assurez-vous que la clé privée existe à l'emplacement configuré\n"
        "3. Ou placez la clé publique dans /app/app/keys/public/public_key.pem"
    )
    
    raise HTTPException(
        status_code=404,
        detail=error_detail
    )