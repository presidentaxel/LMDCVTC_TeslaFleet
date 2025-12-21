# Tesla Fleet API - Backend

API backend FastAPI pour la gestion de la flotte Tesla.

## 🚀 Déploiement avec Docker

### Build l'image Docker

```bash
docker build -t tesla-fleet-backend .
```

### Lancer le conteneur

```bash
docker run -d \
  --name tesla-fleet-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:password@host:5432/dbname \
  -e REDIS_URL=redis://host:6379/0 \
  -e TESLA_CLIENT_ID=your_client_id \
  -e TESLA_CLIENT_SECRET=your_client_secret \
  -e CORS_ORIGINS=https://your-frontend-domain.com \
  -e FRONTEND_URL=https://your-frontend-domain.com \
  tesla-fleet-backend
```

### Variables d'environnement

Créez un fichier `.env` ou configurez les variables suivantes :

- `DATABASE_URL`: URL de connexion PostgreSQL
- `REDIS_URL`: URL de connexion Redis
- `TESLA_CLIENT_ID`: Client ID Tesla (partner)
- `TESLA_CLIENT_SECRET`: Client Secret Tesla (partner)
- `TP_CLIENT_ID`: Client ID pour OAuth third-party
- `TP_CLIENT_SECRET`: Client Secret pour OAuth third-party
- `TP_REDIRECT_URI`: URI de redirection OAuth
- `CORS_ORIGINS`: Origines autorisées (séparées par des virgules)
- `FRONTEND_URL`: URL du frontend pour les redirections OAuth
- `PRIVATE_KEY_PATH`: Chemin vers la clé privée Tesla

### Développement local

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Tests

```bash
pytest
```

## 📦 Structure

```
back/
├── app/
│   ├── api/          # Routes API
│   ├── auth/         # Authentification
│   ├── core/         # Configuration
│   ├── tesla/        # Client Tesla
│   └── main.py       # Point d'entrée
├── requirements.txt
├── Dockerfile
└── README.md
```

