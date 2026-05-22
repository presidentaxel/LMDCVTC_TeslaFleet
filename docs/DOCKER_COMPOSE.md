# 🐳 Docker Compose - Guide d'utilisation

## 🚀 Commandes Principales

### Builder toutes les images

```powershell
docker compose build
```

### Builder sans cache (force rebuild)

```powershell
docker compose build --no-cache
```

### Builder une image spécifique

```powershell
# Backend uniquement
docker compose build backend

# Frontend uniquement
docker compose build frontend
```

### Lancer tous les services

```powershell
docker compose up -d
```

### Lancer et builder en même temps

```powershell
docker compose up -d --build
```

### Voir les logs

```powershell
# Tous les services
docker compose logs -f

# Un service spécifique
docker compose logs -f backend
docker compose logs -f frontend
```

### Arrêter les services

```powershell
docker compose down
```

### Arrêter et supprimer les volumes

```powershell
docker compose down -v
```

## 📦 Services Disponibles

- **backend** : API FastAPI sur le port 8000
- **frontend** : Interface React sur le port 80
- **db** : PostgreSQL sur le port 5432 (optionnel)
- **redis** : Redis sur le port 6379 (optionnel)

## ⚙️ Configuration

Le fichier `docker-compose.yml` configure automatiquement :
- Variables d'environnement pour le backend
- `VITE_API_BASE` pour le frontend au build
- Dépendances entre services
- Volumes pour la persistance

## 🔧 Personnalisation

### Modifier l'URL de l'API pour le frontend

Éditez `docker-compose.yml` et changez :
```yaml
frontend:
  build:
    args:
      VITE_API_BASE: https://api.votre-domaine.com/api  # Changez ici
```

### Désactiver db et redis

Si vous utilisez Supabase ou des services externes, commentez les services dans `docker-compose.yml` :

```yaml
services:
  backend:
    # ...
    # depends_on:
    #   - db
    #   - redis
    environment:
      # DATABASE_URL: postgresql://postgres:postgres@db:5432/postgres
      # REDIS_URL: redis://redis:6379/0
      DATABASE_URL: postgresql://votre-supabase-url
      REDIS_URL: memory://dev  # ou SUPABASE configuré
```

## 🐛 Dépannage

### Erreur: "no configuration file provided"

Assurez-vous d'être à la racine du projet où se trouve `docker-compose.yml`

### Erreur: "port already in use"

Un service utilise déjà le port. Changez le port dans `docker-compose.yml` ou arrêtez le service :

```yaml
ports:
  - "8001:8000"  # Changez 8000 en 8001
```

### Rebuild après modification du code

```powershell
docker compose build --no-cache
docker compose up -d
```

