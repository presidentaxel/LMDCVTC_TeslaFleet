# 🛠️ Guide de Développement Local

Guide pour lancer le backend et le frontend en mode développement local.

## 📋 Prérequis

- **Python 3.11+** avec pip
- **Node.js 20+** avec npm
- **PostgreSQL** (optionnel, peut utiliser SQLite pour le dev)
- **Redis** (optionnel, peut utiliser memory://dev)

## 🚀 Démarrage Rapide

### Option 1: Scripts Automatiques (Recommandé)

**Windows:**
```bash
# Terminal 1 - Backend
cd backend
start-dev.bat

# Terminal 2 - Frontend
cd frontend
start-dev.bat
```

**Linux/Mac:**
```bash
# Terminal 1 - Backend
cd backend
chmod +x start-dev.sh
./start-dev.sh

# Terminal 2 - Frontend
cd frontend
chmod +x start-dev.sh
./start-dev.sh
```

### Option 2: Commandes Manuelles

#### Backend

```bash
cd backend

# Créer un environnement virtuel (recommandé)
python -m venv .venv

# Activer l'environnement virtuel
# Sur Windows:
.venv\Scripts\activate
# Sur Linux/Mac:
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Créer un fichier .env (copier depuis env.example)
cp env.example .env
# Puis éditer .env avec vos valeurs

# Lancer le serveur de développement
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Le backend sera accessible sur: `http://localhost:8000`
- Documentation API: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

#### Frontend

```bash
cd frontend

# Installer les dépendances
npm install

# Créer un fichier .env (copier depuis env.example)
cp env.example .env
# Puis éditer .env avec vos valeurs

# Lancer le serveur de développement
npm run dev
```

Le frontend sera accessible sur: `http://localhost:5173`

## ⚙️ Configuration

### Backend (.env)

Créez un fichier `.env` dans le dossier `backend/`:

```env
# Database (optionnel pour le dev)
DATABASE_URL=sqlite:///./dev.db
# Ou PostgreSQL:
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres

# Redis (optionnel pour le dev)
REDIS_URL=memory://dev
# Ou Redis:
# REDIS_URL=redis://localhost:6379/0

# Tesla Partner Credentials (M2M)
TESLA_CLIENT_ID=your_partner_client_id
TESLA_CLIENT_SECRET=your_partner_client_secret

# Tesla Third-Party OAuth
TP_CLIENT_ID=your_third_party_client_id
TP_CLIENT_SECRET=your_third_party_client_secret
TP_REDIRECT_URI=http://localhost:5173/auth/callback

# Frontend URL
FRONTEND_URL=http://localhost:5173

# CORS Origins
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173

# Private Key Path (optionnel pour le dev)
PRIVATE_KEY_PATH=./app/keys/private/private_key.pem

# Public Key URL
PUBLIC_KEY_URL=http://localhost:8000/.well-known/appspecific/com.tesla.3p.public-key.pem

# Tesla Region
TESLA_REGION=eu

# Environment (dev, staging, prod)
# En dev, CORS accepte toutes les origines pour faciliter le développement
ENV=dev
```

### Frontend (.env)

Créez un fichier `.env` dans le dossier `frontend/`:

```env
# API Backend URL
VITE_API_BASE=http://localhost:8000/api
```

**Note:** Les variables d'environnement Vite doivent commencer par `VITE_` pour être accessibles dans le code.

## 🔧 Commandes Utiles

### Backend

```bash
# Lancer avec auto-reload (développement)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Lancer avec logs détaillés
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# Lancer sur un autre port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Lancer les tests
pytest

# Lancer les tests avec couverture
pytest --cov=app --cov-report=html
```

### Frontend

```bash
# Lancer le serveur de développement
npm run dev

# Builder pour la production
npm run build

# Prévisualiser le build de production
npm run preview

# Linter le code
npm run lint

# Installer une nouvelle dépendance
npm install nom-du-package

# Installer une dépendance de développement
npm install -D nom-du-package
```

## 🐛 Dépannage

### Backend ne démarre pas

**Erreur: Module not found**
```bash
# Réinstaller les dépendances
pip install -r requirements.txt
```

**Erreur: Port déjà utilisé**
```bash
# Utiliser un autre port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

**Erreur: Database connection**
```bash
# Utiliser SQLite pour le dev (pas besoin de PostgreSQL)
DATABASE_URL=sqlite:///./dev.db
```

### Frontend ne démarre pas

**Erreur: Port déjà utilisé**
```bash
# Vite utilisera automatiquement le port suivant disponible
# Ou spécifier un port dans vite.config.ts
```

**Erreur: Cannot find module**
```bash
# Supprimer node_modules et réinstaller
rm -rf node_modules package-lock.json
npm install
```

**Erreur: Variables d'environnement non prises en compte**
- Vérifier que les variables commencent par `VITE_`
- Redémarrer le serveur de développement après modification du `.env`

## 🔄 Workflow de Développement

### 1. Démarrer les services

**Terminal 1 - Backend:**
```bash
cd backend
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 2. Tester les changements

- **Backend:** Les changements sont automatiquement rechargés grâce à `--reload`
- **Frontend:** Vite recompile automatiquement à chaque changement

### 3. Vérifier les logs

- **Backend:** Les logs apparaissent dans le terminal où uvicorn tourne
- **Frontend:** Les logs apparaissent dans le terminal et dans la console du navigateur (F12)

## 📝 Structure des Dossiers

```
tesla-fleet/
├── backend/
│   ├── app/              # Code source
│   │   ├── api/          # Routes API
│   │   ├── auth/         # Authentification
│   │   ├── core/         # Configuration
│   │   └── main.py       # Point d'entrée
│   ├── .env              # Variables d'environnement (à créer)
│   ├── requirements.txt  # Dépendances Python
│   └── pytest.ini        # Configuration tests
│
└── frontend/
    ├── src/              # Code source
    │   ├── components/   # Composants React
    │   ├── features/     # Features
    │   └── lib/          # Utilitaires
    ├── .env              # Variables d'environnement (à créer)
    ├── package.json      # Dépendances Node
    └── vite.config.ts    # Configuration Vite
```

## 🧪 Tests

### Backend

```bash
cd backend

# Lancer tous les tests
pytest

# Lancer un test spécifique
pytest app/tests/test_health.py

# Lancer avec verbosité
pytest -v

# Lancer avec couverture
pytest --cov=app
```

### Frontend

Les tests E2E sont configurés avec Playwright (si disponibles):
```bash
cd frontend
npm run test  # Si configuré
```

## 🔗 URLs de Développement

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/api/health

## 💡 Astuces

1. **Hot Reload:** Les deux serveurs supportent le hot reload automatique
2. **CORS:** Le backend est configuré pour accepter les requêtes depuis `localhost:5173`
3. **Variables d'environnement:** Utilisez `.env` pour ne pas commiter vos secrets
4. **Logs:** Activez `--log-level debug` pour plus de détails
5. **Database:** Utilisez SQLite en dev pour éviter d'installer PostgreSQL

## 🚨 Problèmes Courants

### Le frontend ne peut pas se connecter au backend

**Erreur CORS: "No 'Access-Control-Allow-Origin' header"**

1. Vérifier que le backend tourne sur le port 8000
2. Vérifier `VITE_API_BASE` dans `.env` du frontend
3. **En développement**: Mettre `ENV=dev` dans `.env` du backend pour accepter toutes les origines
4. **En production**: Ajouter votre IP/domaine dans `CORS_ORIGINS` du backend
5. Vérifier la console du navigateur (F12) pour les erreurs CORS

**Solution rapide pour le dev:**
```env
# Dans backend/.env
ENV=dev
```
Cela permet d'accepter toutes les origines en développement.

### Les changements ne se reflètent pas

1. Vérifier que le serveur de dev tourne avec `--reload` (backend)
2. Vérifier que Vite tourne (frontend)
3. Vider le cache du navigateur (Ctrl+Shift+R)
4. Redémarrer les serveurs

### Erreurs de dépendances

**Backend:**
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

**Frontend:**
```bash
rm -rf node_modules package-lock.json
npm install
```

