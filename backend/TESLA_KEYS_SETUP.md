# Configuration des clés Tesla

## Problème

La clé publique Tesla n'est pas accessible à l'URL requise :
```
https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/.well-known/appspecific/com.tesla.3p.public-key.pem
```

## Solution

### Option 1: Générer les clés (si vous n'en avez pas)

Si vous n'avez pas encore de clés Tesla, générez-les :

```bash
cd backend
python scripts/generate_tesla_keys.py
```

Cela créera :
- `app/keys/private/private_key.pem` (clé privée - gardez-la secrète!)
- `app/keys/public/public_key.pem` (clé publique - à héberger)

### Option 2: Utiliser une clé privée existante

Si vous avez déjà une clé privée, configurez `PRIVATE_KEY_PATH` dans vos variables d'environnement DigitalOcean :

```bash
PRIVATE_KEY_PATH=/app/app/keys/private/private_key.pem
```

Le code générera automatiquement la clé publique depuis la clé privée.

### Option 3: Héberger la clé publique manuellement

Si vous avez déjà les deux clés, assurez-vous que :

1. **La clé privée est accessible** à l'emplacement configuré dans `PRIVATE_KEY_PATH`
2. **La clé publique est accessible** à l'un de ces emplacements :
   - `/app/app/keys/public/public_key.pem`
   - `./app/keys/public/public_key.pem`
   - Ou générée automatiquement depuis la clé privée

## Configuration DigitalOcean

Dans DigitalOcean App Platform, configurez :

1. **Variable d'environnement** :
   ```
   PRIVATE_KEY_PATH=/app/app/keys/private/private_key.pem
   ```

2. **Volume ou Secret** :
   - Si vous utilisez un volume Docker, montez-le à `/app/app/keys/`
   - Ou utilisez DigitalOcean Secrets pour stocker la clé privée

3. **Vérifier que la clé est accessible** :
   Le code cherche la clé privée dans plusieurs emplacements :
   - `/app/app/keys/private/private_key.pem`
   - `./app/keys/private/private_key.pem`
   - `/run/secrets/tesla_private_key.pem` (Docker secrets)

## Test

Après configuration, testez :

```bash
curl https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/.well-known/appspecific/com.tesla.3p.public-key.pem
```

Vous devriez voir la clé publique au format PEM.

## Notes importantes

- ⚠️ **Ne partagez JAMAIS votre clé privée**
- ✅ La clé publique peut être publique (c'est son rôle)
- ✅ Le code génère automatiquement la clé publique depuis la clé privée si nécessaire
- ✅ Les clés doivent être en format PEM

