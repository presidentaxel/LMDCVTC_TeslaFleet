# 🚗 Tesla Fleet Management

Application de gestion de flotte Tesla avec backend FastAPI et frontend React/TypeScript.

## 📁 Structure du Projet

```
tesla-fleet/
├── backend/          # API FastAPI (Python)
├── frontend/         # Interface React/TypeScript
├── docs/             # Documentation technique
├── DEV_GUIDE.md      # Guide de développement local
├── DEPLOYMENT.md     # Guide de déploiement
└── TEST_DOCKER.md    # Guide de test Docker
```

## 🚀 Démarrage Rapide

### Développement Local

**Option 1: Scripts automatiques (Windows)**
```bash
# Terminal 1 - Backend
cd backend
start-dev.bat

# Terminal 2 - Frontend
cd frontend
start-dev.bat
```

**Option 2: Commandes manuelles**

**Backend:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
# Backend
docker build -t tesla-fleet-backend ./backend
docker run -d --name tesla-fleet-backend -p 8000:8000 tesla-fleet-backend

# Frontend
docker build --build-arg VITE_API_BASE=http://localhost:8000/api -t tesla-fleet-frontend ./frontend
docker run -d --name tesla-fleet-frontend -p 80:80 tesla-fleet-frontend
```

## 📚 Documentation

- **[Guide de Développement](DEV_GUIDE.md)** - Développement local avec uvicorn et npm
- **[Guide de Déploiement](DEPLOYMENT.md)** - Déploiement en production
- **[Guide Docker](TEST_DOCKER.md)** - Tests avec Docker
- **[Documentation Technique](docs/)** - Architecture et flows

## 🔗 URLs

### Développement
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Production (exemple)
- Frontend: https://app.votre-domaine.com
- Backend API: https://api.votre-domaine.com

## 🛠️ Technologies

### Backend
- **FastAPI** - Framework web Python
- **Uvicorn** - Serveur ASGI
- **PostgreSQL** - Base de données
- **Redis** - Cache et stockage de tokens

### Frontend
- **React 19** - Bibliothèque UI
- **TypeScript** - Typage statique
- **Vite** - Build tool
- **React Router** - Routing

## 📦 Déploiement

Chaque partie peut être déployée indépendamment :

- **Backend** → Docker ou serveur Python
- **Frontend** → Docker (nginx) ou CDN

Voir [DEPLOYMENT.md](DEPLOYMENT.md) pour les détails.

## 🔧 Configuration

### Backend
Copiez `backend/env.example` vers `backend/.env` et configurez vos variables.

**Stockage des tokens** : Par défaut, les tokens sont stockés en mémoire. Pour la production :
- **Redis** : Configurez `REDIS_URL` et `TOKEN_STORE_TYPE=redis`
- **Supabase** (recommandé) : Configurez `SUPABASE_URL`, `SUPABASE_KEY` et `TOKEN_STORE_TYPE=supabase`
  - Voir [SUPABASE_SETUP.md](SUPABASE_SETUP.md) pour la configuration complète

### Frontend
Copiez `frontend/env.example` vers `frontend/.env` et configurez `VITE_API_BASE`.

## 📝 License

[À définir]

## 🤝 Contribution

[À définir]

