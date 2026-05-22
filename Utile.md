# Utile - Gestion LMDC VTC / Tesla Fleet

Référence rapide : commandes **Bash** (Linux, Mac, VPS) et **PowerShell** (Windows).  
Doc détaillée : `docs/TESLA_BUSINESS_SETUP.md`, `docs/API_TESTING.md`, `docs/VEHICLE_COMMANDS.md`, `docs/OVH_SSH_COMMANDS.md`.

---

## Infos projet

| Élément | Valeur |
|---------|--------|
| App Tesla Developer | **GestionLMDCVTC** |
| Client ID OAuth | `0517a56f-d3fd-43f5-9b80-5e15b0488d5f` |
| Domaine API prod | `teslapi.axelproject.fr` |
| VPS OVH | `51.254.128.11` - user `ubuntu` |
| Dossier VPS | `~/LMDCVTC_TeslaFleet` |
| Région Tesla | `eu` (France) |

---

## Ce qu’il manque encore (checklist)

Cocher au fur et à mesure.

### Compte & Tesla

- [ ] **Secret client** collé dans `.env.dev` / `.env.prod` (jamais dans Git)
- [ ] **Consentement business** : Tesla for Business → Account → Consent Management → Request Consent → approuver l’email
- [ ] **Authorization code** échangé (UI Configuration ou `POST /api/business/exchange`)
- [ ] **Au moins un véhicule** dans la flotte Tesla for Business (pour tester commandes / liste)

### Fichiers locaux (non versionnés)

- [ ] `backend/.env.dev` (copie de `backend/env.dev.example`)
- [ ] `backend/.env.prod` (copie de `backend/env.prod.example`) - prod uniquement
- [ ] `frontend/.env` avec `VITE_API_BASE=...`
- [ ] `backend/app/keys/private/private_key.pem` (EC prime256v1, voir génération ci-dessous)

### Infra prod (OVH)

- [ ] DNS `teslapi.axelproject.fr` → `51.254.128.11` (A record)
- [ ] **Caddy** : `/api` et `/.well-known` → `localhost:8000`, reste → `localhost:8080` (voir `deploy/Caddyfile.example`)
- [ ] Racine `.env` : `VITE_API_BASE=https://teslapi.axelproject.fr/api` (copie `env.prod.example`)
- [ ] `docker compose -f docker-compose.prod.yml up -d --build` (frontend sur **8080**, pas 80)
- [ ] `APP_DOMAIN=teslapi.axelproject.fr` et `PUBLIC_KEY_URL=https://teslapi.axelproject.fr/.well-known/...` dans `backend/.env.prod`
- [ ] **Enregistrement domaine Tesla** : `POST /api/fleet/partner/register` (UI Configuration → Infra ou curl)
- [ ] **Clé virtuelle** sur chaque véhicule (pour lock, musique, etc.) - doc Tesla Virtual Keys

### Optionnel

- [ ] Supabase configuré (`TOKEN_STORE_TYPE=supabase`) si multi-utilisateurs / persistance tokens
- [ ] Backend seul : `docker compose -f docker-compose.backend.yml` (sans UI Docker)
- [ ] Refactor gros fichiers backend (`routes_auth`, `oauth_third_party`) - dette technique

---

## Chemins projet

| OS | Racine projet |
|----|----------------|
| Windows | `D:\Code\tesla-fleet` |
| Linux (ex.) | `/home/louitos/Documents/Code/tesla-fleet` |

Adapte `$PROJECT` / `$env:PROJECT` ci-dessous.

---

## 1. Développement local

### 1.1 Première installation

**Bash**

```bash
export PROJECT=/home/louitos/Documents/Code/tesla-fleet
cd "$PROJECT/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp env.dev.example .env.dev
# Éditer .env.dev : TESLA_CLIENT_SECRET=...

cd "$PROJECT/frontend"
npm install
cp env.example .env
```

**PowerShell**

```powershell
$env:PROJECT = "D:\Code\tesla-fleet"
cd "$env:PROJECT\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item env.dev.example .env.dev
# Éditer .env.dev : TESLA_CLIENT_SECRET=...

cd "$env:PROJECT\frontend"
npm install
Copy-Item env.example .env
```

**`.env.dev` minimal (sans Supabase)**

```env
ENV=dev
TOKEN_STORE_TYPE=memory
TESLA_CLIENT_ID=0517a56f-d3fd-43f5-9b80-5e15b0488d5f
TESLA_CLIENT_SECRET=<secret_portail>
TESLA_REGION=eu
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173
PRIVATE_KEY_PATH=./app/keys/private/private_key.pem
PUBLIC_KEY_URL=http://localhost:8000/.well-known/appspecific/com.tesla.3p.public-key.pem
```

### 1.2 Lancer backend + frontend

**Bash - terminal 1 (API)**

```bash
cd "$PROJECT/backend"
source .venv/bin/activate
export ENV=dev
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Bash - terminal 2 (UI)**

```bash
cd "$PROJECT/frontend"
npm run dev
```

**PowerShell - terminal 1**

```powershell
cd "$env:PROJECT\backend"
.\.venv\Scripts\Activate.ps1
$env:ENV = "dev"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**PowerShell - terminal 2**

```powershell
cd "$env:PROJECT\frontend"
npm run dev
```

- UI : http://localhost:5173 → **Configuration** → coller le code business  
- API docs : http://localhost:8000/docs  

**Logs en dev local** : affichés directement dans les terminaux uvicorn (backend) et `npm run dev` (frontend).

### 1.3 Générer les clés Tesla (EC)

**Bash**

```bash
cd "$PROJECT/backend"
source .venv/bin/activate
python scripts/generate_tesla_keys.py
```

**PowerShell**

```powershell
cd "$env:PROJECT\backend"
.\.venv\Scripts\Activate.ps1
python scripts/generate_tesla_keys.py
```

### 1.4 Tests unitaires

**Bash**

```bash
cd "$PROJECT/backend"
source .venv/bin/activate
pip install -r requirements.txt
pytest app/tests/test_business_tokens.py app/tests/test_health.py -q
```

**PowerShell**

```powershell
cd "$env:PROJECT\backend"
.\.venv\Scripts\Activate.ps1
pytest app/tests/test_business_tokens.py app/tests/test_health.py -q
```

### 1.5 Docker local (optionnel)

**Bash / PowerShell** (à la racine du projet)

```bash
docker compose up -d --build
```

Fichier : `docker-compose.yml` + `backend/.env.dev`.

---

## 2. API - curl (local & prod)

Remplacer `BASE` par `http://localhost:8000` ou `https://teslapi.axelproject.fr`.

### 2.1 Santé & statut

**Bash**

```bash
BASE=http://localhost:8000
curl -s "$BASE/api/health" | jq .
curl -s "$BASE/api/business/status" | jq .
curl -s "$BASE/api/business/consent-guide" | jq .
```

**PowerShell**

```powershell
$Base = "http://localhost:8000"
Invoke-RestMethod "$Base/api/health"
Invoke-RestMethod "$Base/api/business/status"
Invoke-RestMethod "$Base/api/business/consent-guide"
```

### 2.2 Échanger le code business (après consentement Tesla)

**Bash**

```bash
BASE=http://localhost:8000
AUTH_CODE="coller_le_code_depuis_consent_management"
curl -s -X POST "$BASE/api/business/exchange" \
  -H "Content-Type: application/json" \
  -d "{\"auth_code\": \"$AUTH_CODE\"}" | jq .
```

**PowerShell**

```powershell
$Base = "http://localhost:8000"
$Body = @{ auth_code = "coller_le_code" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$Base/api/business/exchange" -ContentType "application/json" -Body $Body
```

### 2.3 Liste véhicules

**Bash**

```bash
curl -s "$BASE/api/business/vehicles" | jq .
```

**PowerShell**

```powershell
Invoke-RestMethod "$Base/api/business/vehicles"
```

### 2.4 Commande véhicule (ex. musique, verrou)

`VEHICLE` = ID ou VIN depuis la liste.

**Bash**

```bash
VEHICLE=1234567890
# Piste suivante
curl -s -X POST "$BASE/api/business/vehicles/$VEHICLE/commands/media_next_track" \
  -H "Content-Type: application/json" \
  -d '{"body": {}}' | jq .

# Verrouiller
curl -s -X POST "$BASE/api/business/vehicles/$VEHICLE/commands/door_lock" \
  -H "Content-Type: application/json" \
  -d '{"body": {}}' | jq .

# Volume (corps JSON requis)
curl -s -X POST "$BASE/api/business/vehicles/$VEHICLE/commands/adjust_volume" \
  -H "Content-Type: application/json" \
  -d '{"body": {"volume": 5}}' | jq .
```

**PowerShell**

```powershell
$Vehicle = "1234567890"
$Body = '{"body": {}}'
Invoke-RestMethod -Method Post -Uri "$Base/api/business/vehicles/$Vehicle/commands/media_next_track" -ContentType "application/json" -Body $Body

$BodyVol = '{"body": {"volume": 5}}'
Invoke-RestMethod -Method Post -Uri "$Base/api/business/vehicles/$Vehicle/commands/adjust_volume" -ContentType "application/json" -Body $BodyVol
```

### 2.5 Infra partenaire (prod, une fois)

**Bash**

```bash
BASE=https://teslapi.axelproject.fr
curl -s "$BASE/api/fleet/partner/token-debug?refresh=1" | jq .
curl -s -X POST "$BASE/api/fleet/partner/register" | jq .
curl -s "$BASE/.well-known/appspecific/com.tesla.3p.public-key.pem"
```

**PowerShell**

```powershell
$Base = "https://teslapi.axelproject.fr"
Invoke-RestMethod "$Base/api/fleet/partner/token-debug?refresh=1"
Invoke-RestMethod -Method Post -Uri "$Base/api/fleet/partner/register"
curl.exe "$Base/.well-known/appspecific/com.tesla.3p.public-key.pem"
```

### 2.6 Catalogue commandes (API)

**Bash**

```bash
curl -s "$BASE/api/business/commands/catalog" | jq .
```

Liste complète : `docs/VEHICLE_COMMANDS.md`.

---

## 3. Déploiement OVH (prod)

### 3.1 Git - pousser le code

**Bash**

```bash
cd "$PROJECT"
git status
git add .
git commit -m "votre message"
git push origin main
```

**PowerShell**

```powershell
cd $env:PROJECT
git status
git add .
git commit -m "votre message"
git push origin main
```

### 3.2 Copier secrets vers le VPS (si modifiés)

**PowerShell**

```powershell
scp "$env:PROJECT\backend\.env.prod" ubuntu@51.254.128.11:~/LMDCVTC_TeslaFleet/backend/.env.prod
scp "$env:PROJECT\backend\app\keys\private\private_key.pem" ubuntu@51.254.128.11:~/LMDCVTC_TeslaFleet/backend/app/keys/private/private_key.pem
```

**Bash (depuis Linux)**

```bash
scp "$PROJECT/backend/.env.prod" ubuntu@51.254.128.11:~/LMDCVTC_TeslaFleet/backend/.env.prod
scp "$PROJECT/backend/app/keys/private/private_key.pem" ubuntu@51.254.128.11:~/LMDCVTC_TeslaFleet/backend/app/keys/private/private_key.pem
```

### 3.3 SSH + rebuild sur le VPS

**Bash (PC)**

```bash
ssh ubuntu@51.254.128.11
```

**Bash (sur le VPS)**

```bash
cd ~/LMDCVTC_TeslaFleet
git pull origin main

cp -n env.prod.example .env
# nano .env  → VITE_API_BASE=https://teslapi.axelproject.fr/api

docker compose -f docker-compose.prod.yml up -d --build
docker ps
```

### 3.4 Caddy (HTTPS + routage UI / API)

**Bash (VPS)**

```bash
sudo cp ~/LMDCVTC_TeslaFleet/deploy/Caddyfile.example /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
sudo systemctl status caddy
```

Détail : `docs/OVH_SSH_COMMANDS.md` et `deploy/Caddyfile.example`.

### 3.5 Vérifications prod

**Bash (VPS)**

```bash
curl -s http://localhost:8000/api/health
curl -s http://localhost:8000/api/business/status
curl -sI http://localhost:8080/ | head -5
curl -s http://localhost:8000/.well-known/appspecific/com.tesla.3p.public-key.pem | head -3
```

**PowerShell (PC)**

```powershell
curl.exe https://teslapi.axelproject.fr/api/health
curl.exe https://teslapi.axelproject.fr/api/business/status
nslookup teslapi.axelproject.fr 8.8.8.8
```

### 3.6 Logs Docker (backend + frontend)

Sur le VPS, depuis `~/LMDCVTC_TeslaFleet`. Fichier compose : `docker-compose.prod.yml` (services `backend` et `frontend`).

**Dernières lignes (sans suivre en direct)**

```bash
cd ~/LMDCVTC_TeslaFleet

# Backend (API FastAPI / uvicorn)
docker compose -f docker-compose.prod.yml logs --tail=100 backend

# Frontend (nginx dans le conteneur)
docker compose -f docker-compose.prod.yml logs --tail=100 frontend

# Les deux en même temps
docker compose -f docker-compose.prod.yml logs --tail=100 backend frontend
```

**Suivre les logs en direct** (`Ctrl+C` pour quitter) :

```bash
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f backend frontend
```

**Logs depuis un moment** (ex. 10 dernières minutes) :

```bash
docker compose -f docker-compose.prod.yml logs --since=10m backend
docker compose -f docker-compose.prod.yml logs --since=10m frontend
```

**Backend seul** (sans conteneur frontend) :

```bash
docker compose -f docker-compose.backend.yml logs -f --tail=100 backend
```

**Logs nginx à l’intérieur du frontend** (si la page ne charge pas) :

```bash
docker compose -f docker-compose.prod.yml exec frontend cat /var/log/nginx/error.log
```

**Caddy** (HTTPS, routage - pas Docker) :

```bash
sudo journalctl -u caddy -f
sudo journalctl -u caddy --since "1 hour ago" --no-pager
```

### 3.7 Dépannage : `/api/business/*` en 404

**Symptôme** : la console affiche 404 sur `api/business/status`, `consent-guide`, `vehicles`, alors que `/api/health` répond 200.

**Cause** : le **frontend** est rebuild depuis le code (`git pull`), mais le **backend** tournait encore avec l’ancienne image Docker Hub `thelouitos/tesla-fleet-backend:latest`, publiée **avant** les routes business.

**Correction** (sur le VPS, après `git pull` avec `docker-compose.prod.yml` qui inclut `build: ./backend`) :

```bash
cd ~/LMDCVTC_TeslaFleet
docker compose -f docker-compose.prod.yml up -d --build backend
curl -s http://localhost:8000/api/business/status
curl -s http://localhost:8000/api/business/consent-guide | head -c 200
```

Réponse attendue pour `status` : JSON (pas HTML, pas 404).  
Lister les routes : `curl -s http://localhost:8000/openapi.json | grep business`

**Alternative** : repousser l’image Hub depuis ton PC (`docs/BUILD_AND_PUSH.md`) puis `docker compose pull backend` sur le VPS.

---

## 4. Récap commandes une ligne

| Action | Bash (VPS / local) | PowerShell (PC) |
|--------|-------------------|-----------------|
| SSH VPS | `ssh ubuntu@51.254.128.11` | `ssh ubuntu@51.254.128.11` |
| API health local | `curl -s localhost:8000/api/health` | `Invoke-RestMethod http://localhost:8000/api/health` |
| API health prod | `curl -s https://teslapi.axelproject.fr/api/health` | `curl.exe https://teslapi.axelproject.fr/api/health` |
| Rebuild Docker VPS | `docker compose -f docker-compose.prod.yml up -d --build` | - (après SSH) |
| Logs backend VPS | `docker compose -f docker-compose.prod.yml logs -f --tail=100 backend` | - (après SSH) |
| Logs frontend VPS | `docker compose -f docker-compose.prod.yml logs -f --tail=100 frontend` | - (après SSH) |
| Logs Caddy | `sudo journalctl -u caddy -f` | - |
| Reload Caddy | `sudo systemctl reload caddy` | - |
| UI locale | ouvrir http://localhost:5173 | idem |
| Swagger | http://localhost:8000/docs | idem |

---

## 5. Ordre recommandé (première mise en route)

1. Créer `.env.dev` + coller **TESLA_CLIENT_SECRET**  
2. Générer clés EC → lancer backend + frontend en local  
3. Consentement sur **Tesla for Business** → coller code dans l’UI **Configuration**  
4. Tester `GET /api/business/vehicles` (vide tant qu’aucun véhicule)  
5. Déployer sur OVH → Caddy HTTPS → `partner/register`  
6. Ajouter véhicule à la flotte → tester **Commandes** (média, lock, …)

---

## 6. Liens utiles

- Portail dev : https://developer.tesla.com  
- Tesla for Business : https://www.tesla.com/teslaaccount/business  
- Doc token business : https://developer.tesla.com/docs/fleet-api/authentication/third-party-business-tokens  
- Commandes véhicule : https://developer.tesla.com/docs/fleet-api/endpoints/vehicle-commands  
