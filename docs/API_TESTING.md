# Tester l’API (curl & UI)

## GET — lire une information

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/business/status
curl http://localhost:8000/api/business/consent-guide
```

## POST — déclencher une action

### Échanger le code business (après consentement Tesla)

```bash
curl -X POST http://localhost:8000/api/business/exchange \
  -H "Content-Type: application/json" \
  -d '{"auth_code": "VOTRE_CODE_ICI"}'
```

### Liste véhicules

```bash
curl http://localhost:8000/api/business/vehicles
```

### Commande véhicule

```bash
curl -X POST "http://localhost:8000/api/business/vehicles/ID/commands/door_lock" \
  -H "Content-Type: application/json" \
  -d '{"body": {}}'
```

### Enregistrer le domaine (prod, une fois)

```bash
curl -X POST http://localhost:8000/api/fleet/partner/register
```

## Swagger

http://localhost:8000/docs — bouton **Try it out** sur chaque route.

## UI (recommandé)

http://localhost:5173 → **Configuration** → un bouton pour valider le consentement.
