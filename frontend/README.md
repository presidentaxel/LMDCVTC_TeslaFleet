# Tesla Fleet - Frontend

Interface web React/TypeScript pour la gestion de la flotte Tesla.

## 🚀 Déploiement avec Docker

### Build l'image Docker

```bash
docker build -t tesla-fleet-frontend .
```

### Lancer le conteneur

```bash
docker run -d \
  --name tesla-fleet-frontend \
  -p 80:80 \
  -e VITE_API_BASE=https://your-backend-domain.com/api \
  tesla-fleet-frontend
```

**Note:** Pour la production, vous devez builder l'application avec les bonnes variables d'environnement avant de créer l'image Docker, car Vite les injecte au moment du build.

### Build avec variables d'environnement

```bash
# Créer un fichier .env.production
echo "VITE_API_BASE=https://your-backend-domain.com/api" > .env.production

# Builder l'application
npm run build

# Puis builder l'image Docker
docker build -t tesla-fleet-frontend .
```

### Variables d'environnement

- `VITE_API_BASE`: URL de base de l'API backend (ex: `https://api.example.com/api`)

### Développement local

```bash
# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

L'application sera accessible sur `http://localhost:5173`

### Build pour production

```bash
npm run build
```

Les fichiers seront générés dans le dossier `dist/`

## 📦 Structure

```
front/
├── src/
│   ├── components/   # Composants React
│   ├── features/      # Features de l'application
│   ├── lib/          # Utilitaires et API client
│   └── main.tsx      # Point d'entrée
├── public/           # Fichiers statiques
├── package.json
├── Dockerfile
└── README.md
```

## 🔗 Configuration de l'API

Le frontend se connecte au backend via la variable d'environnement `VITE_API_BASE`. Assurez-vous que cette variable pointe vers votre backend en production.
