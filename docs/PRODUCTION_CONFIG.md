# 🔧 Configuration pour la Production Docker

Guide pour configurer les clés privées/publiques et les URLs pour la production avec Docker.

## 📋 Variables d'Environnement Importantes

### 1. `PRIVATE_KEY_PATH`

**Développement local:**
```bash
PRIVATE_KEY_PATH=./app/keys/private/private_key.pem
```

**Production Docker:**
```bash
PRIVATE_KEY_PATH=/app/app/keys/private/private_key.pem
```

Le volume Docker monte `backend_keys` vers `/app/app/keys`, donc vos clés doivent être dans ce volume.

### 2. `PUBLIC_KEY_URL`

**Développement local:**
```bash
PUBLIC_KEY_URL=http://localhost:8000/.well-known/appspecific/com.tesla.3p.public-key.pem
```

**Production Docker:**
```bash
PUBLIC_KEY_URL=https://votre-domaine.com/.well-known/appspecific/com.tesla.3p.public-key.pem
```

⚠️ **IMPORTANT**: 
- Remplacez `votre-domaine.com` par votre vrai domaine public
- Cette URL doit être accessible publiquement par Tesla (HTTPS requis)
- L'endpoint est automatiquement servi par le backend à cette route

### 3. `APP_DOMAIN`

**Développement local:**
```bash
APP_DOMAIN=  # Peut être omis
```

**Production Docker:**
```bash
APP_DOMAIN=votre-domaine.com
```

⚠️ **IMPORTANT**: 
- Domaine sans `http://` ou `https://`
- Ce domaine doit être enregistré dans le portail Tesla Developer
- Utilisé pour l'enregistrement partenaire via `/api/fleet/partner/register`

## 🚀 Configuration Docker Compose pour la Production

### Option 1: Variables dans docker-compose.yml

Ajoutez ces variables dans la section `environment` du service `backend`:

```yaml
backend:
  environment:
    # ... autres variables ...
    
    # Chemin vers la clé privée dans le conteneur
    PRIVATE_KEY_PATH: /app/app/keys/private/private_key.pem
    
    # URL publique de votre clé (remplacez par votre domaine)
    PUBLIC_KEY_URL: https://votre-domaine.com/.well-known/appspecific/com.tesla.3p.public-key.pem
    
    # Domaine de votre application
    APP_DOMAIN: votre-domaine.com
    
    # Environment
    ENV: prod
```

### Option 2: Fichier .env

Créez un fichier `.env` à la racine du projet:

```bash
# Backend - Production
PRIVATE_KEY_PATH=/app/app/keys/private/private_key.pem
PUBLIC_KEY_URL=https://votre-domaine.com/.well-known/appspecific/com.tesla.3p.public-key.pem
APP_DOMAIN=votre-domaine.com
ENV=prod
```

Puis référencez-le dans `docker-compose.yml`:

```yaml
backend:
  env_file:
    - .env
```

## 📁 Structure des Clés dans Docker

Les clés sont stockées dans un volume Docker nommé `backend_keys`:

```
/app/app/keys/
├── private/
│   └── private_key.pem    # Clé privée (requise)
└── public/
    └── public_key.pem     # Clé publique (optionnelle, générée automatiquement si absente)
```

### Comment ajouter vos clés au volume Docker

**Option 1: Copier après le démarrage du conteneur**

```bash
# Démarrer les conteneurs
docker compose up -d

# Copier la clé privée
docker cp ./backend/app/keys/private/private_key.pem tesla-fleet-backend-1:/app/app/keys/private/private_key.pem

# Optionnel: Copier la clé publique si vous l'avez
docker cp ./backend/app/keys/public/public_key.pem tesla-fleet-backend-1:/app/app/keys/public/public_key.pem
```

**Option 2: Montage direct (développement uniquement)**

```yaml
backend:
  volumes:
    - ./backend/app/keys:/app/app/keys  # Montage direct (dev uniquement)
```

⚠️ **Note**: En production, utilisez un volume nommé pour la sécurité.

## ✅ Vérification

### 1. Vérifier que l'endpoint de clé publique fonctionne

```bash
# En local
curl http://localhost:8000/.well-known/appspecific/com.tesla.3p.public-key.pem

# En production
curl https://votre-domaine.com/.well-known/appspecific/com.tesla.3p.public-key.pem
```

Vous devriez recevoir le contenu de la clé publique au format PEM.

### 2. Vérifier la configuration

```bash
# Vérifier les variables d'environnement dans le conteneur
docker compose exec backend env | grep -E "PRIVATE_KEY_PATH|PUBLIC_KEY_URL|APP_DOMAIN"
```

### 3. Tester l'enregistrement partenaire

```bash
# Appeler l'endpoint d'enregistrement
curl -X POST http://localhost:8000/api/fleet/partner/register
```

## 🔐 Sécurité

1. **Ne commitez jamais vos clés privées** dans Git
2. **Utilisez des secrets** pour stocker les clés en production (Docker secrets, Kubernetes secrets, etc.)
3. **HTTPS obligatoire** en production pour `PUBLIC_KEY_URL`
4. **Restreignez l'accès** au volume `backend_keys` aux seuls conteneurs nécessaires

## 📝 Exemple Complet

Voici un exemple de configuration complète pour la production:

```yaml
# docker-compose.prod.yml
services:
  backend:
    environment:
      PRIVATE_KEY_PATH: /app/app/keys/private/private_key.pem
      PUBLIC_KEY_URL: https://api.mon-app.com/.well-known/appspecific/com.tesla.3p.public-key.pem
      APP_DOMAIN: api.mon-app.com
      ENV: prod
      # ... autres variables ...
```

Et dans votre fichier `.env` ou variables d'environnement du serveur:

```bash
PRIVATE_KEY_PATH=/app/app/keys/private/private_key.pem
PUBLIC_KEY_URL=https://api.mon-app.com/.well-known/appspecific/com.tesla.3p.public-key.pem
APP_DOMAIN=api.mon-app.com
```

## 🆘 Dépannage

### Erreur: "Clé publique non trouvée"

1. Vérifiez que `PRIVATE_KEY_PATH` pointe vers le bon fichier
2. Vérifiez que le fichier existe dans le volume Docker
3. Vérifiez les permissions du fichier

### Erreur: "APP_DOMAIN manquant"

Assurez-vous que `APP_DOMAIN` est défini avant d'appeler `/api/fleet/partner/register`.

### L'endpoint de clé publique retourne 404

1. Vérifiez que le backend est démarré
2. Vérifiez que l'endpoint est accessible publiquement (pas de firewall)
3. Vérifiez que vous utilisez HTTPS en production

## OVH : Caddy + Docker (frontend visible)

Sur le VPS, **Caddy** utilise les ports 80/443. Le frontend Docker doit écouter sur **8080**, pas 80.

1. `cp env.prod.example .env` - définir `VITE_API_BASE=https://votre-domaine.com/api`
2. `docker compose -f docker-compose.prod.yml up -d --build`
3. Copier `deploy/Caddyfile.example` vers `/etc/caddy/Caddyfile` et recharger Caddy

Si `https://votre-domaine.com/` affiche `{"detail":"Not Found"}`, Caddy envoie encore tout vers le backend : mettre à jour le Caddyfile (routes `/api` → `:8000`, reste → `:8080`).

Guide détaillé : [OVH_SSH_COMMANDS.md](./OVH_SSH_COMMANDS.md).

