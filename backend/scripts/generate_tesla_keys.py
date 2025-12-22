#!/usr/bin/env python3
"""
Script pour générer une paire de clés RSA pour Tesla Fleet API.
Utilisez ce script si vous n'avez pas encore de clés.
"""
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from pathlib import Path
import os

def generate_tesla_keys():
    """Génère une paire de clés RSA pour Tesla."""
    # Créer les répertoires si nécessaire
    private_dir = Path("./app/keys/private")
    public_dir = Path("./app/keys/public")
    
    private_dir.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)
    
    # Générer la clé privée
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Sauvegarder la clé privée
    private_key_path = private_dir / "private_key.pem"
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    with open(private_key_path, "wb") as f:
        f.write(private_pem)
    
    print(f"✓ Clé privée générée: {private_key_path}")
    print(f"  Permissions: {oct(private_key_path.stat().st_mode)[-3:]}")
    
    # Générer la clé publique
    public_key = private_key.public_key()
    public_key_path = public_dir / "public_key.pem"
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    with open(public_key_path, "wb") as f:
        f.write(public_pem)
    
    print(f"✓ Clé publique générée: {public_key_path}")
    print(f"  Permissions: {oct(public_key_path.stat().st_mode)[-3:]}")
    
    # Afficher la clé publique pour copier-coller si nécessaire
    print("\n" + "="*70)
    print("CLÉ PUBLIQUE (à héberger sur votre serveur):")
    print("="*70)
    print(public_pem.decode())
    print("="*70)
    
    print("\n✓ Clés générées avec succès!")
    print(f"\nConfigurez dans votre .env:")
    print(f"  PRIVATE_KEY_PATH={private_key_path.absolute()}")
    print(f"  PUBLIC_KEY_URL=https://votre-domaine.com/.well-known/appspecific/com.tesla.3p.public-key.pem")
    
    # Sécuriser les permissions (uniquement sur Unix)
    if os.name != 'nt':
        os.chmod(private_key_path, 0o600)
        os.chmod(public_key_path, 0o644)
        print("\n✓ Permissions sécurisées (600 pour privée, 644 pour publique)")

if __name__ == "__main__":
    try:
        generate_tesla_keys()
    except Exception as e:
        print(f"❌ Erreur lors de la génération des clés: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

