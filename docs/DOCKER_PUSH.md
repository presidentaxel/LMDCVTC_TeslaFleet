# 🐳 Push des Images Docker vers Docker Hub

Guide pour tagger et pousser les images backend et frontend vers Docker Hub.

## 📋 Prérequis

1. Avoir un compte sur [Docker Hub](https://hub.docker.com)
2. Être connecté : `docker login`
3. Avoir buildé les images localement

## 🚀 Commandes Rapides

### Frontend

```powershell
docker tag tesla-fleet-frontend thelouitos/tesla-fleet-frontend:latest; if ($?) { docker push thelouitos/tesla-fleet-frontend:latest }
```

### Backend

```powershell
docker tag tesla-fleet-backend thelouitos/tesla-fleet-backend:latest; if ($?) { docker push thelouitos/tesla-fleet-backend:latest }
```

## 📝 Étapes Détaillées

### 1. Builder les images

**Frontend:**
```powershell
cd frontend
docker build --build-arg VITE_API_BASE=https://api.votre-domaine.com/api -t tesla-fleet-frontend .
```

**Backend:**
```powershell
cd backend
docker build -t tesla-fleet-backend .
```

### 2. Tagger les images

**Frontend:**
```powershell
docker tag tesla-fleet-frontend thelouitos/tesla-fleet-frontend:latest
```

**Backend:**
```powershell
docker tag tesla-fleet-backend thelouitos/tesla-fleet-backend:latest
```

### 3. Pousser vers Docker Hub

**Frontend:**
```powershell
docker push thelouitos/tesla-fleet-frontend:latest
```

**Backend:**
```powershell
docker push thelouitos/tesla-fleet-backend:latest
```

## 🔄 Workflow Complet

### Option 1: Commandes Séparées

```powershell
# Frontend
cd frontend
docker build --build-arg VITE_API_BASE=https://api.votre-domaine.com/api -t tesla-fleet-frontend .
docker tag tesla-fleet-frontend thelouitos/tesla-fleet-frontend:latest
docker push thelouitos/tesla-fleet-frontend:latest

# Backend
cd ..\backend
docker build -t tesla-fleet-backend .
docker tag tesla-fleet-backend thelouitos/tesla-fleet-backend:latest
docker push thelouitos/tesla-fleet-backend:latest
```

### Option 2: Avec Vérification (comme votre exemple)

**Frontend:**
```powershell
docker tag tesla-fleet-frontend thelouitos/tesla-fleet-frontend:latest; if ($?) { docker push thelouitos/tesla-fleet-frontend:latest }
```

**Backend:**
```powershell
docker tag tesla-fleet-backend thelouitos/tesla-fleet-backend:latest; if ($?) { docker push thelouitos/tesla-fleet-backend:latest }
```

## 🎯 Scripts Automatisés

### Script PowerShell Complet

Créez `push-images.ps1` :

```powershell
# Configuration
$DOCKER_USER = "thelouitos"
$FRONTEND_IMAGE = "tesla-fleet-frontend"
$BACKEND_IMAGE = "tesla-fleet-backend"
$VITE_API_BASE = "https://api.votre-domaine.com/api"  # À adapter

Write-Host "🚀 Build et Push des images Docker" -ForegroundColor Cyan

# Frontend
Write-Host "`n📦 Building frontend..." -ForegroundColor Yellow
Set-Location frontend
docker build --build-arg VITE_API_BASE=$VITE_API_BASE -t $FRONTEND_IMAGE .
if ($?) {
    docker tag "$FRONTEND_IMAGE" "$DOCKER_USER/$FRONTEND_IMAGE`:latest"
    if ($?) {
        docker push "$DOCKER_USER/$FRONTEND_IMAGE`:latest"
        Write-Host "✅ Frontend pushed successfully" -ForegroundColor Green
    }
}

# Backend
Write-Host "`n📦 Building backend..." -ForegroundColor Yellow
Set-Location ..\backend
docker build -t $BACKEND_IMAGE .
if ($?) {
    docker tag "$BACKEND_IMAGE" "$DOCKER_USER/$BACKEND_IMAGE`:latest"
    if ($?) {
        docker push "$DOCKER_USER/$BACKEND_IMAGE`:latest"
        Write-Host "✅ Backend pushed successfully" -ForegroundColor Green
    }
}

Set-Location ..
Write-Host "`n✨ Done!" -ForegroundColor Green
```

### Utilisation

```powershell
.\push-images.ps1
```

## 🔐 Authentification Docker Hub

Si vous n'êtes pas connecté :

```powershell
docker login
# Entrez votre username et password Docker Hub
```

## 📦 Pull depuis Docker Hub

Une fois poussé, vous pouvez pull depuis n'importe où :

```powershell
# Frontend
docker pull thelouitos/tesla-fleet-frontend:latest

# Backend
docker pull thelouitos/tesla-fleet-backend:latest
```

## 🏷️ Tags et Versions

Pour pousser avec des versions spécifiques :

```powershell
# Frontend v1.0.0
docker tag tesla-fleet-frontend thelouitos/tesla-fleet-frontend:1.0.0
docker tag tesla-fleet-frontend thelouitos/tesla-fleet-frontend:latest
docker push thelouitos/tesla-fleet-frontend:1.0.0
docker push thelouitos/tesla-fleet-frontend:latest

# Backend v1.0.0
docker tag tesla-fleet-backend thelouitos/tesla-fleet-backend:1.0.0
docker tag tesla-fleet-backend thelouitos/tesla-fleet-backend:latest
docker push thelouitos/tesla-fleet-backend:1.0.0
docker push thelouitos/tesla-fleet-backend:latest
```

## ⚠️ Notes Importantes

1. **Variables d'environnement Frontend** : N'oubliez pas de définir `VITE_API_BASE` au build
2. **Secrets** : Ne commitez jamais les secrets dans les images
3. **Taille des images** : Utilisez `.dockerignore` pour réduire la taille
4. **Multi-stage builds** : Déjà configurés dans les Dockerfiles

## 🔍 Vérification

Après le push, vérifiez sur Docker Hub :
- https://hub.docker.com/r/thelouitos/tesla-fleet-frontend
- https://hub.docker.com/r/thelouitos/tesla-fleet-backend

