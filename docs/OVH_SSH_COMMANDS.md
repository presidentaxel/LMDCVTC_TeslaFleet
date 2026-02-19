# Commandes SSH et déploiement OVH

Récapitulatif des commandes pour le VPS OVH (backend Tesla Fleet).

---

## Déploiement complet : push vers le VPS (étapes dans l’ordre)

À faire **sur ton PC (PowerShell)** puis **sur le VPS (SSH)**.

### 1. Sur le PC — Git (pousser le code)

```powershell
cd D:\Code\tesla-fleet

git status
git add .
git commit -m "ton message"
git push origin main
```

### 2. Sur le PC — Envoyer les fichiers sensibles (si modifiés)

À faire seulement si tu as changé `.env.prod` ou la clé privée Tesla :

```powershell
# Fichier d'environnement prod
scp D:\Code\tesla-fleet\backend\.env.prod ubuntu@51.254.128.11:~/LMDCVTC_TeslaFleet/backend/.env.prod

# Clé privée Tesla (EC prime256v1) — si tu l'as régénérée
scp D:\Code\tesla-fleet\backend\app\keys\private\private_key.pem ubuntu@51.254.128.11:~/LMDCVTC_TeslaFleet/backend/keys/private/private_key.pem
```

Si sur le VPS la clé est dans `backend/app/keys/private/`, utilise plutôt :

```powershell
scp D:\Code\tesla-fleet\backend\app\keys\private\private_key.pem ubuntu@51.254.128.11:~/LMDCVTC_TeslaFleet/backend/app/keys/private/private_key.pem
```

### 3. Sur le VPS — Récupérer le code et redémarrer

Connexion SSH :

```bash
ssh ubuntu@51.254.128.11
```

Puis sur le VPS :

```bash
cd ~/LMDCVTC_TeslaFleet

# Récupérer les derniers changements
git pull origin main

# Reconstruire et redémarrer le backend
docker compose -f docker-compose.backend.yml up -d --build

# (Optionnel) Forcer recréation des conteneurs
# docker compose -f docker-compose.backend.yml up -d --force-recreate
```

### 4. Vérifications

Sur le VPS :

```bash
# Santé de l’API
curl http://localhost:8000/api/health

# Clé publique Tesla (doit afficher un bloc PEM court, EC)
curl http://localhost:8000/.well-known/appspecific/com.tesla.3p.public-key.pem
```

Depuis ton PC :

```powershell
curl.exe https://teslapi.axelproject.fr/api/health
curl.exe https://teslapi.axelproject.fr/.well-known/appspecific/com.tesla.3p.public-key.pem
```

---

## Connexion SSH

```bash
ssh ubuntu@51.254.128.11
```

Ou avec le nom du VPS :

```bash
ssh ubuntu@vps-2c7db76a.vps.ovh.net
```

---

## Chemins sur le VPS

- Projet : `~/LMDCVTC_TeslaFleet`
- Backend : `~/LMDCVTC_TeslaFleet/backend`
- Env prod : `~/LMDCVTC_TeslaFleet/backend/.env.prod`
- Clé privée Tesla : `~/LMDCVTC_TeslaFleet/backend/keys/private/private_key.pem`

---

## Backend (Docker)

Se placer dans le projet :

```bash
cd ~/LMDCVTC_TeslaFleet
```

Lancer le backend :

```bash
docker compose -f docker-compose.backend.yml up -d --build
```

Arrêter :

```bash
docker compose -f docker-compose.backend.yml down
```

Voir les logs :

```bash
docker compose -f docker-compose.backend.yml logs -f
```

Vérifier que le backend répond (sur le VPS) :

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/.well-known/appspecific/com.tesla.3p.public-key.pem
```

---

## Caddy (HTTPS)

Configurer le domaine (remplacer `teslapi.axelproject.fr` par ton domaine) :

```bash
sudo nano /etc/caddy/Caddyfile
```

Exemple de contenu :

```
teslapi.axelproject.fr {
    reverse_proxy localhost:8000
}
```

Recharger Caddy :

```bash
sudo systemctl reload caddy
```

Vérifier le statut :

```bash
sudo systemctl status caddy
```

---

## Copier des fichiers depuis ton PC (Windows)

Dans **PowerShell**, depuis ton PC :

Clé privée Tesla vers le VPS :

```powershell
scp D:\Code\tesla-fleet\backend\app\keys\private\private_key.pem ubuntu@51.254.128.11:~/LMDCVTC_TeslaFleet/backend/keys/private/private_key.pem
```

Fichier `.env.prod` vers le VPS :

```powershell
scp D:\Code\tesla-fleet\backend\.env.prod ubuntu@51.254.128.11:~/LMDCVTC_TeslaFleet/backend/.env.prod
```

Adapte les chemins (`D:\Code\tesla-fleet`) si ton projet est ailleurs.

---

## Vérifications utiles

Sur le VPS (après connexion SSH) :

- Fichier clé présent : `ls -la ~/LMDCVTC_TeslaFleet/backend/keys/private/private_key.pem`
- Conteneurs : `docker ps`
- Logs backend : `docker compose -f docker-compose.backend.yml logs -f backend`

Depuis ton PC (PowerShell) :

- Test API par IP : `curl.exe http://51.254.128.11:8000/api/health`
- Test DNS : `nslookup teslapi.axelproject.fr 8.8.8.8`
- Test HTTPS (une fois le domaine résolu et Caddy en place) : `curl.exe https://teslapi.axelproject.fr/api/health`

---

## Récap rapide

| Action              | Commande |
|---------------------|----------|
| Se connecter au VPS | `ssh ubuntu@51.254.128.11` |
| Aller au projet     | `cd ~/LMDCVTC_TeslaFleet` |
| Pull + rebuild      | `git pull origin main` puis `docker compose -f docker-compose.backend.yml up -d --build` |
| Démarrer le backend | `docker compose -f docker-compose.backend.yml up -d --build` |
| Voir les logs       | `docker compose -f docker-compose.backend.yml logs -f` |
| Recharger Caddy     | `sudo systemctl reload caddy` |
