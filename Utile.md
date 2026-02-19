# SSH
ssh ubuntu@51.254.128.11

# Caddy (HTTPS)
sudo systemctl status caddy
sudo systemctl reload caddy

# Docker
docker compose -f docker-compose.backend.yml up -d --build
# force recréation si besoin :
docker compose -f docker-compose.backend.yml up -d --force-recreate

# --- Push vers le VPS (tout le workflow) ---
# 1. PC : push le code
git add .
git commit -m "message"
git push origin main

# 2. PC : envoyer .env et clé si modifiés
scp D:\Code\tesla-fleet\backend\.env.prod ubuntu@51.254.128.11:~/LMDCVTC_TeslaFleet/backend/.env.prod
scp D:\Code\tesla-fleet\backend\app\keys\private\private_key.pem ubuntu@51.254.128.11:~/LMDCVTC_TeslaFleet/backend/keys/private/private_key.pem

# 3. VPS (après ssh) : pull + rebuild
cd ~/LMDCVTC_TeslaFleet
git pull origin main
docker compose -f docker-compose.backend.yml up -d --build

