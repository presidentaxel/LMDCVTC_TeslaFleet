# ⚡ Commandes Rapides - Push Docker Hub

## 🎯 Commandes Copy-Paste (PowerShell)

### Frontend
```powershell
docker tag tesla-fleet-frontend thelouitos/tesla-fleet-frontend:latest; if ($?) { docker push thelouitos/tesla-fleet-frontend:latest }
```

### Backend
```powershell
docker tag tesla-fleet-backend thelouitos/tesla-fleet-backend:latest; if ($?) { docker push thelouitos/tesla-fleet-backend:latest }
```

## 📋 Prérequis

1. **Builder les images d'abord** :
```powershell
# Frontend
cd frontend
docker build --build-arg VITE_API_BASE=https://api.votre-domaine.com/api -t tesla-fleet-frontend .

# Backend
cd ..\backend
docker build -t tesla-fleet-backend .
```

2. **Se connecter à Docker Hub** :
```powershell
docker login
```

3. **Puis utiliser les commandes ci-dessus**

## 🔄 Tout en Une Ligne

Si vous voulez build + tag + push en une commande :

**Frontend:**
```powershell
cd frontend; docker build --build-arg VITE_API_BASE=https://api.votre-domaine.com/api -t tesla-fleet-frontend .; docker tag tesla-fleet-frontend thelouitos/tesla-fleet-frontend:latest; if ($?) { docker push thelouitos/tesla-fleet-frontend:latest }
```

**Backend:**
```powershell
cd backend; docker build -t tesla-fleet-backend .; docker tag tesla-fleet-backend thelouitos/tesla-fleet-backend:latest; if ($?) { docker push thelouitos/tesla-fleet-backend:latest }
```

## 🚀 Script Automatique

Utilisez le script `push-images.ps1` pour tout automatiser :

```powershell
.\push-images.ps1
```

