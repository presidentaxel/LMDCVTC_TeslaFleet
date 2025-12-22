# 🚀 Build et Push - Guide Complet

## 🔧 Problèmes Résolus

### 1. Image frontend manquante

L'image `tesla-fleet-frontend` n'existe pas. Vous avez `tesla-fleet-frontend-debug` mais pas la version de production.

**Solution : Builder l'image frontend**

```powershell
cd frontend
docker build --build-arg VITE_API_BASE=http://localhost:8000/api -t tesla-fleet-frontend .
cd ..
```

### 2. Docker Compose

Le fichier `docker-compose.yml` existe bien. Utilisez :

```powershell
docker compose build --no-cache
```

**Note :** Utilisez `docker compose` (avec espace) et non `docker-compose` (avec tiret).

## 📦 Workflow Complet

### Option 1: Docker Compose (Recommandé)

```powershell
# Builder toutes les images
docker compose build --no-cache

# Vérifier les images créées
docker images | Select-String "tesla-fleet"

# Tagger et pousser
docker tag tesla-fleet-backend thelouitos/tesla-fleet-backend:latest; if ($?) { docker push thelouitos/tesla-fleet-backend:latest }
docker tag tesla-fleet-frontend thelouitos/tesla-fleet-frontend:latest; if ($?) { docker push thelouitos/tesla-fleet-frontend:latest }
```

### Option 2: Build Manuel

```powershell
# Backend
cd backend
docker build -t tesla-fleet-backend .
cd ..

# Frontend
cd frontend
docker build --build-arg VITE_API_BASE=http://localhost:8000/api -t tesla-fleet-frontend .
cd ..

# Tagger et pousser
docker tag tesla-fleet-backend thelouitos/tesla-fleet-backend:latest; if ($?) { docker push thelouitos/tesla-fleet-backend:latest }
docker tag tesla-fleet-frontend thelouitos/tesla-fleet-frontend:latest; if ($?) { docker push thelouitos/tesla-fleet-frontend:latest }
```

## 🔄 Git Remote

Votre remote pointe vers un autre repo. Pour le changer :

```powershell
# Supprimer l'ancien remote
git remote remove origin

# Ajouter le nouveau
git remote add origin https://github.com/presidentaxel/LMDCVTC_TeslaFleet.git

# Vérifier
git remote -v

# Pousser
git push -u origin main
```

## ✅ Checklist Avant Push

- [ ] Images Docker buildées (`docker images | Select-String "tesla-fleet"`)
- [ ] Connecté à Docker Hub (`docker login`)
- [ ] Remote Git configuré (`git remote -v`)
- [ ] `.env` fichiers non commités (vérifier avec `git status`)

