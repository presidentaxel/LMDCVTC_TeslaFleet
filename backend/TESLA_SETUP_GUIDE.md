# Guide de configuration Tesla Fleet API

## Configuration requise

D'après votre portail Tesla Developer, votre application utilise :
- **Client ID**: `cacad6ff-48dd-4e8f-b521-8180d0865b94`
- **Types d'autorisation**: `client-credentials` (partner) et `authorization-code` (third-party)
- **Domaine**: `https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/`

## Configuration des variables d'environnement

### Pour les tokens partenaires (M2M - client-credentials)

```bash
TESLA_CLIENT_ID=cacad6ff-48dd-4e8f-b521-8180d0865b94
TESLA_CLIENT_SECRET=<votre_client_secret>
```

**Note importante**: Pour les tokens partenaires, vous devez utiliser le **même CLIENT_ID** que pour les tokens utilisateurs, mais avec `grant_type=client_credentials`.

### Pour les tokens utilisateurs (Third-Party OAuth - authorization-code)

```bash
TP_CLIENT_ID=cacad6ff-48dd-4e8f-b521-8180d0865b94
TP_CLIENT_SECRET=<votre_client_secret>
TP_REDIRECT_URI=https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/api/auth/callback
```

**Note**: Vous pouvez utiliser le même CLIENT_ID et CLIENT_SECRET pour les deux types de tokens.

### Configuration du domaine

```bash
APP_DOMAIN=lmdcvtc-teslafleet-huukv.ondigitalocean.app
PUBLIC_KEY_URL=https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/.well-known/appspecific/com.tesla.3p.public-key.pem
```

## Étapes de configuration

### 1. Enregistrer le domaine partenaire (OBLIGATOIRE)

Avant de pouvoir obtenir des tokens partenaires, vous **DEVEZ** enregistrer votre domaine :

```bash
POST /api/fleet/partner/register
```

Cet endpoint :
- Utilise un token partenaire temporaire (ou les credentials directement)
- Enregistre votre domaine avec Tesla
- Doit être fait **une fois par région** (EU et NA)

**Important**: Si vous obtenez une erreur 403 lors de l'obtention du token partenaire, c'est peut-être parce que le domaine n'a pas encore été enregistré.

### 2. Vérifier la configuration

```bash
GET /api/fleet/partner/token-debug
```

Cet endpoint vous dira :
- Si les credentials sont configurés
- Si le token partenaire peut être obtenu
- L'erreur exacte si quelque chose ne va pas

### 3. Obtenir un token utilisateur

Pour les endpoints utilisateurs, utilisez le flux OAuth :

```bash
GET /api/auth/login
```

Puis complétez l'authentification dans le navigateur.

## Problème courant : Erreur 403 sur les tokens partenaires

Si vous obtenez une erreur 403 lors de l'obtention d'un token partenaire, cela peut être dû à :

1. **Domaine non enregistré** : Vous devez d'abord appeler `/api/fleet/partner/register`
2. **Credentials incorrects** : Vérifiez que `TESLA_CLIENT_ID` et `TESLA_CLIENT_SECRET` sont corrects
3. **Permissions manquantes** : Vérifiez dans le portail Tesla que les permissions partenaire sont activées

## Solution recommandée

Si vous utilisez le même CLIENT_ID pour les deux types de tokens (ce qui est correct), configurez :

```bash
# Les deux peuvent utiliser le même CLIENT_ID
TESLA_CLIENT_ID=cacad6ff-48dd-4e8f-b521-8180d0865b94
TESLA_CLIENT_SECRET=<votre_secret>

TP_CLIENT_ID=cacad6ff-48dd-4e8f-b521-8180d0865b94
TP_CLIENT_SECRET=<votre_secret>
```

Puis, **enregistrez d'abord le domaine** avant d'essayer d'obtenir des tokens partenaires.

