# 🚀 Déploiement sur DigitalOcean App Platform

Guide complet pour déployer Tesla Fleet sur DigitalOcean App Platform.

## 📋 Prérequis

1. Compte DigitalOcean
2. Repository GitHub avec votre code
3. Clés Tesla (privée et publique)

## 🔧 Configuration

### 1. Fichier `.do/app.yaml`

Le fichier `.do/app.yaml` configure votre application pour DigitalOcean App Platform. 

**⚠️ IMPORTANT**: Mettez à jour les valeurs suivantes :
- `repo`: Votre nom d'utilisateur GitHub et nom du repository
- `branch`: Votre branche de déploiement (généralement `main`)

### 2. Variables d'Environnement (App-Level)

Dans DigitalOcean, allez dans **Settings > App-Level Environment Variables** et ajoutez :

#### Variables Requises

```bash
# Database (si vous utilisez un database component)
# Sinon, utilisez une base de données externe
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis (si vous utilisez un Redis component)
# Sinon, utilisez un Redis externe ou memory://dev pour le dev
REDIS_URL=redis://host:6379/0

# Environment
ENV=prod

# Tesla Partner Credentials (M2M)
TESLA_CLIENT_ID=votre_partner_client_id
TESLA_CLIENT_SECRET=votre_partner_client_secret

# Tesla Third-Party OAuth
TP_CLIENT_ID=votre_third_party_client_id
TP_CLIENT_SECRET=votre_third_party_client_secret
TP_REDIRECT_URI=https://votre-domaine.com/auth/callback

# Frontend URL
FRONTEND_URL=https://votre-domaine.com

# CORS Origins
CORS_ORIGINS=https://votre-domaine.com

# ⚠️ IMPORTANT: Configuration des clés
PRIVATE_KEY_PATH=/app/app/keys/private/private_key.pem
PUBLIC_KEY_URL=https://votre-domaine.com/.well-known/appspecific/com.tesla.3p.public-key.pem
APP_DOMAIN=votre-domaine.com

# Tesla Region
TESLA_REGION=eu
```

### 3. Configuration du Health Check

Le health check est configuré dans `.do/app.yaml` :

```yaml
health_check:
  http_path: /api/health
  initial_delay_seconds: 30
  period_seconds: 10
  timeout_seconds: 5
  success_threshold: 1
  failure_threshold: 3
```

**Port**: Le backend écoute sur le port **8000** (configuré dans `http_port: 8000`).

**⚠️ Si vous voyez une erreur "connection refused on port 8080"** :
- Vérifiez que `http_port: 8000` est bien défini dans `.do/app.yaml`
- Vérifiez que le Dockerfile expose le port 8000 : `EXPOSE 8000`
- Vérifiez que uvicorn écoute sur le port 8000 : `--port 8000`

### 4. Stockage des Clés Privées

DigitalOcean App Platform ne supporte pas directement les volumes Docker comme dans docker-compose. Vous avez plusieurs options :

#### Option A: Variables d'Environnement (Base64)

1. Encoder votre clé privée en base64 :
```bash
cat private_key.pem | base64
```

2. Ajouter comme variable d'environnement :
```bash
PRIVATE_KEY_B64=<votre_clé_encodée_en_base64>
```

3. Modifier le code pour décoder la clé au démarrage (nécessite une modification du code)

#### Option B: DigitalOcean Spaces (Recommandé)

1. Uploader vos clés dans un DigitalOcean Space (S3-compatible)
2. Télécharger les clés au démarrage de l'application
3. Stocker temporairement dans `/tmp` ou `/app/app/keys`

#### Option C: Secrets Management

Utiliser un service de gestion de secrets (HashiCorp Vault, AWS Secrets Manager, etc.)

#### Option D: Build-time (Non recommandé pour la sécurité)

Inclure les clés dans l'image Docker (⚠️ **NON SÉCURISÉ**)

### 5. Configuration du Frontend

Le frontend doit être configuré avec l'URL de l'API backend :

```yaml
envs:
  - key: VITE_API_BASE
    scope: BUILD_TIME
    value: ${APP_URL}/api
```

`${APP_URL}` sera automatiquement remplacé par l'URL de votre application DigitalOcean.

## 🚀 Déploiement

### Méthode 1: Via l'Interface DigitalOcean

1. Allez sur [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Cliquez sur **Create App**
3. Connectez votre repository GitHub
4. DigitalOcean détectera automatiquement le fichier `.do/app.yaml`
5. Configurez les variables d'environnement
6. Déployez

### Méthode 2: Via l'API DigitalOcean

```bash
doctl apps create --spec .do/app.yaml
```

## ✅ Vérification

### 1. Vérifier le Health Check

```bash
curl https://votre-domaine.com/api/health
```

Devrait retourner :
```json
{"status": "ok"}
```

### 2. Vérifier la Clé Publique

```bash
curl https://votre-domaine.com/.well-known/appspecific/com.tesla.3p.public-key.pem
```

Devrait retourner le contenu de la clé publique au format PEM.

### 3. Vérifier les Logs

Dans DigitalOcean, allez dans **Runtime Logs** pour voir les logs de votre application.

## 🔍 Dépannage

### Erreur: "Readiness probe failed: dial tcp ...:8080: connect: connection refused"

**Cause**: DigitalOcean essaie de se connecter sur le port 8080 au lieu de 8000.

**Solution**:
1. Vérifiez que `http_port: 8000` est défini dans `.do/app.yaml`
2. Vérifiez que le Dockerfile expose le port 8000
3. Vérifiez que uvicorn écoute sur le port 8000

### Erreur: "Clé publique non trouvée"

**Cause**: Les clés ne sont pas accessibles dans le conteneur.

**Solution**:
1. Vérifiez que `PRIVATE_KEY_PATH` pointe vers le bon chemin
2. Vérifiez que les clés sont bien uploadées/téléchargées
3. Vérifiez les permissions des fichiers

### Erreur: "Application startup failed"

**Cause**: Erreur au démarrage de l'application (base de données, Redis, etc.)

**Solution**:
1. Vérifiez les logs dans DigitalOcean
2. Vérifiez que toutes les variables d'environnement sont définies
3. Vérifiez que les services externes (DB, Redis) sont accessibles

## 📝 Notes Importantes

1. **Port**: Le backend doit écouter sur le port **8000** (pas 8080)
2. **Health Check**: L'endpoint `/api/health` doit être accessible
3. **HTTPS**: DigitalOcean fournit automatiquement HTTPS
4. **Variables d'Environnement**: Utilisez App-Level Environment Variables pour la sécurité
5. **Secrets**: Ne commitez jamais vos clés privées dans Git

## 🔐 Sécurité

1. Utilisez **App-Level Environment Variables** pour les secrets
2. Ne commitez jamais les clés privées
3. Utilisez HTTPS (automatique avec DigitalOcean)
4. Restreignez les CORS origins en production
5. Utilisez des variables d'environnement pour toutes les configurations sensibles

## 📚 Ressources

- [DigitalOcean App Platform Documentation](https://docs.digitalocean.com/products/app-platform/)
- [App Spec Reference](https://docs.digitalocean.com/products/app-platform/reference/app-spec/)

