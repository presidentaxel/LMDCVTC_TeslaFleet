# Correction des problèmes de production

## Problèmes identifiés et solutions

### ✅ 1. Clé publique Tesla - RÉSOLU
**Problème** : La clé publique n'était pas accessible  
**Solution** : Le code génère maintenant automatiquement la clé publique depuis la clé privée  
**Test** : `curl https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/.well-known/appspecific/com.tesla.3p.public-key.pem` → ✅ 200 OK

### ✅ 2. Token partenaire - RÉSOLU
**Problème** : Erreur 403 lors de l'obtention du token partenaire  
**Solution** : Configuration correcte des credentials (TESLA_CLIENT_ID/SECRET)  
**Test** : `/api/fleet/partner/token-debug` → ✅ Token valide

### ⚠️ 3. Endpoints partenaires qui timeout (502)
**Problème** : Les endpoints suivants retournent 502 "via_upstream" :
- `/api/fleet/partner/telemetry-errors`
- `/api/fleet/partner/register`
- `/api/fleet/partner/public-key`

**Causes possibles** :
1. **Timeout DigitalOcean App Platform** : Le timeout par défaut peut être trop court
2. **Timeout API Tesla** : L'API Tesla peut prendre plus de 15 secondes à répondre
3. **Crash de l'application** : Une erreur non gérée peut faire planter l'application

**Solutions appliquées** :
- ✅ Gestion améliorée des erreurs avec messages détaillés
- ✅ Gestion spécifique des timeouts (504 au lieu de 502)
- ✅ Meilleure gestion des erreurs HTTP de Tesla

**Recommandations** :
1. **Augmenter le timeout dans DigitalOcean** :
   - Allez dans App Platform → Settings → Health Checks
   - Augmentez le timeout à 30-60 secondes

2. **Augmenter HTTP_TIMEOUT_SECONDS** :
   ```bash
   HTTP_TIMEOUT_SECONDS=30
   ```

3. **Vérifier les logs DigitalOcean** :
   - Consultez les logs pour voir l'erreur exacte
   - Les logs devraient maintenant contenir plus d'informations

### ⚠️ 4. Erreur OAuth 403
**Problème** : Erreur 403 lors de l'échange du code OAuth  
**URL d'erreur** : `https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/auth?error=Client%20error%20%27403%20Forbidden%27...`

**Causes possibles** :
1. **TP_CLIENT_ID ou TP_CLIENT_SECRET incorrects** : Vérifiez que vous utilisez les bons credentials
2. **Code expiré** : Les codes OAuth expirent rapidement (quelques minutes)
3. **PKCE verifier manquant** : Le state a expiré ou n'a pas été stocké correctement
4. **Redirect URI mismatch** : Le redirect_uri ne correspond pas exactement à celui configuré dans le portail Tesla

**Solutions appliquées** :
- ✅ Messages d'erreur détaillés avec causes possibles
- ✅ Affichage du TP_CLIENT_ID et TP_REDIRECT_URI utilisés
- ✅ Meilleure gestion des erreurs dans le callback

**Vérifications à faire** :
1. **Vérifier TP_CLIENT_ID et TP_CLIENT_SECRET** :
   ```bash
   TP_CLIENT_ID=cacad6ff-48dd-4e8f-b521-8180d0865b94
   TP_CLIENT_SECRET=ta-secret.fuzqgw206NrIUVNW
   ```

2. **Vérifier TP_REDIRECT_URI** :
   ```bash
   TP_REDIRECT_URI=https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/api/auth/callback
   ```
   Doit correspondre EXACTEMENT à celui configuré dans le portail Tesla Developer

3. **Vérifier dans le portail Tesla** :
   - Allez dans https://developer.tesla.com
   - Vérifiez que l'URI de redirection est exactement : `https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/api/auth/callback`

## Configuration recommandée pour production

```bash
# Timeouts
HTTP_TIMEOUT_SECONDS=30

# Tesla Partner (M2M)
TESLA_CLIENT_ID=cacad6ff-48dd-4e8f-b521-8180d0865b94
TESLA_CLIENT_SECRET=ta-secret.fuzqgw206NrIUVNW

# Tesla Third-Party OAuth
TP_CLIENT_ID=cacad6ff-48dd-4e8f-b521-8180d0865b94
TP_CLIENT_SECRET=ta-secret.fuzqgw206NrIUVNW
TP_REDIRECT_URI=https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/api/auth/callback

# Domain
APP_DOMAIN=lmdcvtc-teslafleet-huukv.ondigitalocean.app
PUBLIC_KEY_URL=https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/.well-known/appspecific/com.tesla.3p.public-key.pem
PRIVATE_KEY_PATH=/app/app/keys/private/private_key.pem
```

## Prochaines étapes

1. ✅ Clé publique fonctionne
2. ✅ Token partenaire fonctionne
3. ⚠️ Augmenter les timeouts dans DigitalOcean et dans la config
4. ⚠️ Vérifier les logs DigitalOcean pour les erreurs 502
5. ⚠️ Vérifier la configuration OAuth dans le portail Tesla

## Tests à effectuer

```bash
# 1. Clé publique (devrait fonctionner)
curl https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/.well-known/appspecific/com.tesla.3p.public-key.pem

# 2. Token partenaire (devrait fonctionner)
curl https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/api/fleet/partner/token-debug

# 3. Status (devrait fonctionner)
curl https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/api/fleet/status

# 4. Register (peut timeout - vérifier les logs)
curl -X POST https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/api/fleet/partner/register

# 5. OAuth login (tester le flux complet)
# Aller sur https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/api/auth/login
```

