# 🔧 Dépannage Frontend Docker

## Problèmes courants

### 1. Le build échoue

**Symptôme:** `docker build` échoue avec une erreur

**Solution:**
```bash
# Tester le build localement d'abord
cd frontend
npm install
npm run build

# Si ça fonctionne localement, le problème est dans Docker
# Vérifier les logs détaillés
docker build --progress=plain --build-arg VITE_API_BASE=http://localhost:8000/api -t tesla-fleet-frontend . 2>&1 | tee build.log
```

### 2. Le conteneur démarre mais le site ne s'affiche pas

**Vérifications:**
```bash
# Vérifier que le conteneur tourne
docker ps | grep frontend

# Vérifier les logs
docker logs tesla-fleet-frontend

# Vérifier que les fichiers sont présents dans le conteneur
docker exec tesla-fleet-frontend ls -la /usr/share/nginx/html/

# Tester nginx
docker exec tesla-fleet-frontend nginx -t
```

### 3. Erreur 502 ou connexion refusée

**Causes possibles:**
- Nginx n'a pas démarré
- Les fichiers dist/ ne sont pas présents
- Le port est déjà utilisé

**Solutions:**
```bash
# Vérifier si le port 80 est utilisé
netstat -ano | findstr :80

# Utiliser un autre port
docker run -d --name tesla-fleet-frontend -p 8080:80 tesla-fleet-frontend

# Vérifier les logs nginx
docker exec tesla-fleet-frontend cat /var/log/nginx/error.log
```

### 4. Build réussit mais dist/ est vide

**Solution:**
```bash
# Utiliser le Dockerfile de debug
docker build -f Dockerfile.debug -t tesla-fleet-frontend-debug .
docker run -it --rm -p 5173:5173 tesla-fleet-frontend-debug

# Vérifier manuellement dans le conteneur
docker run -it --rm tesla-fleet-frontend-debug sh
# Puis dans le conteneur:
ls -la dist/
cat dist/index.html
```

### 5. Variables d'environnement non prises en compte

**Important:** Vite injecte les variables au moment du build, pas au runtime.

**Solution:**
```bash
# Toujours utiliser --build-arg
docker build --build-arg VITE_API_BASE=https://api.votre-domaine.com/api -t tesla-fleet-frontend .
```

## Commandes de debug utiles

```bash
# Build avec logs détaillés
docker build --progress=plain --no-cache --build-arg VITE_API_BASE=http://localhost:8000/api -t tesla-fleet-frontend .

# Lancer en mode interactif pour debug
docker run -it --rm -p 80:80 tesla-fleet-frontend sh

# Vérifier la configuration nginx
docker exec tesla-fleet-frontend cat /etc/nginx/conf.d/default.conf

# Tester nginx manuellement
docker exec tesla-fleet-frontend nginx -t
docker exec tesla-fleet-frontend nginx -s reload
```

## Build local pour tester

Avant de builder avec Docker, testez localement:

```bash
cd frontend
npm install
npm run build
ls -la dist/  # Vérifier que dist/ contient les fichiers
```

Si le build local fonctionne mais pas Docker, le problème est dans le Dockerfile.

