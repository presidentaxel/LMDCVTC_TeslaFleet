# Configuration Tesla for Business — Gestion LMDC VTC

Guide local → production (`teslapi.axelproject.fr`).

## Client OAuth (GestionLMDCVTC)

| Variable | Valeur |
|----------|--------|
| `TESLA_CLIENT_ID` | `0517a56f-d3fd-43f5-9b80-5e15b0488d5f` |
| `TESLA_CLIENT_SECRET` | Secret affiché dans le portail (œil) — **jamais dans Git** |

## Le consentement : ordre des opérations

**Non**, le code ne *demande* pas le consentement à Tesla. C’est normal :

1. Un humain (admin business) approuve sur **Tesla for Business** (portail web Tesla).
2. Vous récupérez l’**authorization code** dans Consent Management.
3. **Votre app** échange ce code contre un token (`POST /api/business/exchange`).

L’UI **Configuration → Valider le consentement** fait l’étape 3.

### Étapes portail Tesla for Business

1. [Tesla for Business](https://www.tesla.com/teslaaccount/business)
2. **Account** → **Consent Management**
3. **Request Consent** → app **GestionLMDCVTC** → email admin
4. Approuver l’email `noreply@tesla.com`
5. Copier le code → coller dans l’app

## Développement local

### Backend

```bash
cd backend
cp env.dev.example .env.dev
# Éditer .env.dev : TESLA_CLIENT_SECRET=...
export ENV=dev
export TOKEN_STORE_TYPE=memory
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
cp env.example .env
npm install
npm run dev
```

Ouvrir http://localhost:5173 → **Configuration** → coller le code business.

### Tests

```bash
cd backend && pytest app/tests/test_business_tokens.py app/tests/test_health.py -q
```

## Production OVH

1. `.env.prod` avec `APP_DOMAIN=teslapi.axelproject.fr`, HTTPS, secret Tesla.
2. Clé EC : `python scripts/generate_tesla_keys.py`
3. Déployer backend + frontend.
4. UI **Configuration → Infra** : enregistrer le domaine Tesla.
5. Consentement business + véhicules dans la flotte.

## Commandes à distance

Scope `vehicle_cmds` + **clé virtuelle** sur le véhicule. Voir [VEHICLE_COMMANDS.md](./VEHICLE_COMMANDS.md).
