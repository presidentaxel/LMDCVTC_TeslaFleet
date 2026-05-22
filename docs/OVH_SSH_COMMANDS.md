# Commandes SSH et déploiement OVH

Récapitulatif pour le VPS OVH : **Caddy** (HTTPS, ports 80/443) + **Docker** (backend `:8000`, frontend `:8080`).

---

## Architecture prod

| Service | Port hôte | Rôle |
|---------|-----------|------|
| Caddy | 80, 443 | HTTPS, routage vers backend / frontend |
| Backend (Docker) | 8000 | API FastAPI, clé publique Tesla |
| Frontend (Docker) | 8080 | UI React (nginx) |

Caddy ne doit **pas** tout envoyer vers le backend : la racine `/` doit aller vers le frontend, sinon vous verrez `{"detail":"Not Found"}` (réponse FastAPI).

Fichier de référence : [`deploy/Caddyfile.example`](../deploy/Caddyfile.example).

---

## Déploiement complet (étapes dans l’ordre)

### 1. Sur le PC - Git

```powershell
cd D:\Code\tesla-fleet
git add .
git commit -m "votre message"
git push origin main
```

### 2. Sur le PC - Fichiers sensibles (si modifiés)

```powershell
scp D:\Code\tesla-fleet\backend\.env.prod ubuntu@51.254.128.11:~/LMDCVTC_TeslaFleet/backend/.env.prod
scp D:\Code\tesla-fleet\backend\app\keys\private\private_key.pem ubuntu@51.254.128.11:~/LMDCVTC_TeslaFleet/backend/keys/private/private_key.pem
```

### 3. Sur le VPS - Pull, variables, Docker

```bash
ssh ubuntu@51.254.128.11
cd ~/LMDCVTC_TeslaFleet
git pull origin main

# Variables de build frontend (une fois, ou après changement de domaine)
cp -n env.prod.example .env
# nano .env   → VITE_API_BASE=https://teslapi.axelproject.fr/api

docker compose -f docker-compose.prod.yml up -d --build
docker ps
```

Le conteneur `frontend` doit être **Up** et mapper `0.0.0.0:8080->80/tcp`.  
Si vous voyez `address already in use` sur le port **80**, c’est normal avec l’ancienne config : le repo utilise maintenant **8080**.

### 4. Sur le VPS - Caddy

```bash
sudo cp ~/LMDCVTC_TeslaFleet/deploy/Caddyfile.example /etc/caddy/Caddyfile
# Adapter le nom de domaine si besoin :
# sudo nano /etc/caddy/Caddyfile

sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
sudo systemctl status caddy
```

### 5. Vérifications

**Sur le VPS :**

```bash
curl -s http://localhost:8000/api/health
curl -sI http://localhost:8080/ | head -5
curl -s http://localhost:8080/ | head -c 200
```

**Depuis le PC :**

```powershell
curl.exe https://teslapi.axelproject.fr/api/health
curl.exe -I https://teslapi.axelproject.fr/
```

- `/api/health` → JSON `{"status":"ok"}` (ou équivalent)
- `/` → `Content-Type: text/html` (page React), pas `{"detail":"Not Found"}`

---

## Connexion SSH

```bash
ssh ubuntu@51.254.128.11
```

---

## Chemins sur le VPS

| Élément | Chemin |
|---------|--------|
| Projet | `~/LMDCVTC_TeslaFleet` |
| Env backend | `~/LMDCVTC_TeslaFleet/backend/.env.prod` |
| Env build frontend | `~/LMDCVTC_TeslaFleet/.env` (copie de `env.prod.example`) |
| Clé privée Tesla | `~/LMDCVTC_TeslaFleet/backend/keys/private/private_key.pem` |
| Caddy | `/etc/caddy/Caddyfile` |

---

## Docker

### Backend + frontend (recommandé)

```bash
cd ~/LMDCVTC_TeslaFleet
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml down
```

### Backend seul

```bash
docker compose -f docker-compose.backend.yml up -d --build
```

---

## Caddy (HTTPS + routage)

Exemple complet (déjà dans `deploy/Caddyfile.example`) :

```caddy
teslapi.axelproject.fr {
	handle /api/* {
		reverse_proxy localhost:8000
	}

	handle /.well-known/* {
		reverse_proxy localhost:8000
	}

	handle {
		reverse_proxy localhost:8080
	}
}
```

```bash
sudo systemctl reload caddy
```

---

## Dépannage rapide

| Symptôme | Cause probable | Action |
|----------|----------------|--------|
| `{"detail":"Not Found"}` sur `/` | Caddy envoie tout vers `:8000` | Mettre à jour le Caddyfile (frontend → `:8080`) |
| `failed to bind ... :80` | Conflit Caddy / ancien compose | Utiliser `8080:80` dans `docker-compose.prod.yml` |
| UI charge mais API en erreur | Mauvais `VITE_API_BASE` au build | Corriger `.env`, puis `docker compose ... up -d --build` |
| `/api/health` OK, `/api/business/*` 404 | Image backend Hub obsolète | `docker compose -f docker-compose.prod.yml up -d --build backend` |
| Frontend absent dans `docker ps` | Échec au démarrage (port, build) | `docker compose -f docker-compose.prod.yml logs frontend` |

Vérifier ce qui occupe le port 80 :

```bash
sudo ss -tlnp | grep ':80 '
docker ps -a
```

---

## Récap rapide

| Action | Commande |
|--------|----------|
| SSH | `ssh ubuntu@51.254.128.11` |
| Pull + deploy | `cd ~/LMDCVTC_TeslaFleet && git pull && docker compose -f docker-compose.prod.yml up -d --build` |
| Reload Caddy | `sudo systemctl reload caddy` |
| Logs | `docker compose -f docker-compose.prod.yml logs -f` |
