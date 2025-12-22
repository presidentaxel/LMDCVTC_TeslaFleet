# Fix pour l'endpoint `/api/fleet/partner/register`

## Problème

L'endpoint retourne une erreur 502 "via_upstream" de DigitalOcean App Platform, ce qui indique que :
- Soit l'application crash avant de répondre
- Soit il y a un timeout au niveau de la plateforme
- Soit il y a une erreur non gérée qui fait planter l'application

## Solution

### 1. Vérifier la configuration

Assurez-vous que `APP_DOMAIN` est bien configuré dans vos variables d'environnement :

```bash
APP_DOMAIN=lmdcvtc-teslafleet-huukv.ondigitalocean.app
PUBLIC_KEY_URL=https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/.well-known/appspecific/com.tesla.3p.public-key.pem
```

### 2. Vérifier que la clé publique est accessible

Testez que votre clé publique est accessible :

```bash
curl https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/.well-known/appspecific/com.tesla.3p.public-key.pem
```

### 3. Vérifier les logs

Consultez les logs de votre application dans DigitalOcean App Platform pour voir l'erreur exacte.

### 4. Test avec un timeout plus long

Si c'est un problème de timeout, vous pouvez augmenter `HTTP_TIMEOUT_SECONDS` dans vos variables d'environnement :

```bash
HTTP_TIMEOUT_SECONDS=30
```

### 5. Test de l'endpoint avec plus de détails

L'endpoint devrait maintenant retourner des erreurs plus détaillées. Si vous obtenez toujours une erreur 502, cela signifie que l'application crash avant d'atteindre le code de gestion d'erreurs.

## Diagnostic

Pour diagnostiquer le problème :

1. **Vérifier que le token partenaire fonctionne** :
   ```bash
   curl -X 'GET' 'https://lmdcvtc-teslafleet-huukv.ondigitalocean.app/api/fleet/partner/token-debug'
   ```
   ✅ Cela fonctionne maintenant !

2. **Vérifier la configuration du domaine** :
   L'endpoint devrait maintenant valider le domaine avant d'appeler Tesla.

3. **Vérifier les logs DigitalOcean** :
   Les logs devraient maintenant contenir plus d'informations sur l'erreur.

## Note importante

Si le domaine est déjà enregistré, Tesla retournera une erreur 409, ce qui est normal. L'endpoint devrait maintenant gérer cela correctement.

