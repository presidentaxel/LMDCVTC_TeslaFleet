# Guide de dépannage

## Problèmes courants et solutions

### ❌ Erreur 403 Forbidden lors de l'obtention du token partenaire

**Symptôme:**
```json
{
  "error": "Client error '403 Forbidden' for url 'https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token'"
}
```

**Causes possibles:**

1. **Credentials partenaires incorrects**
   - `TESLA_CLIENT_ID` ou `TESLA_CLIENT_SECRET` sont incorrects
   - Les credentials sont pour un environnement différent (staging vs production)

2. **Application non configurée dans le portail Tesla Developer**
   - L'application n'existe pas dans le portail Tesla Developer
   - L'application n'a pas les permissions partenaire activées

3. **Mauvais environnement**
   - Les credentials sont pour un environnement différent (EU vs NA, staging vs production)

**Solutions:**

1. **Vérifier les credentials:**
   ```bash
   curl -X 'GET' 'https://votre-domaine.com/api/fleet/partner/token-debug'
   ```
   Cela vous dira si les credentials sont configurés et quelle erreur exacte Tesla retourne.

2. **Vérifier dans le portail Tesla Developer:**
   - Connectez-vous à https://developer.tesla.com
   - Vérifiez que votre application existe
   - Vérifiez que les permissions partenaire sont activées
   - Vérifiez que vous utilisez les bons credentials (production vs staging)

3. **Vérifier la région:**
   - Assurez-vous que `TESLA_REGION` correspond à la région de vos credentials
   - EU pour Europe/Middle East/Africa
   - NA pour North America/Asia Pacific

---

### ❌ Erreur 502 lors de l'enregistrement partenaire

**Symptôme:**
```
Error: We encountered an error when trying to load your application
via_upstream (502 -)
```

**Causes possibles:**

1. **Token partenaire non disponible** (erreur 403 lors de l'obtention du token)
2. **Domaine invalide** (localhost non accepté par Tesla)
3. **Erreur non gérée dans le code**

**Solutions:**

1. **Vérifier le token partenaire:**
   ```bash
   curl -X 'GET' 'https://votre-domaine.com/api/fleet/partner/token-debug'
   ```
   Si cela retourne une erreur 403, résolvez d'abord ce problème.

2. **Vérifier le domaine:**
   - Tesla n'accepte **PAS** `localhost`, `127.0.0.1`, ou les adresses IP privées
   - Utilisez un vrai domaine (ex: `example.com`)
   - Pour le développement, utilisez ngrok ou Cloudflare Tunnel

3. **Vérifier les logs de l'application:**
   - Consultez les logs dans DigitalOcean App Platform
   - Recherchez les erreurs détaillées

---

### ❌ Erreur "Invalid domain: localhost"

**Symptôme:**
```json
{
  "error": "Invalid domain: localhost. Ensure that domain is lowercase and starts without https://"
}
```

**Solution:**

Tesla n'accepte pas `localhost` pour l'enregistrement partenaire. Vous devez utiliser un vrai domaine.

**Options:**

1. **Utiliser ngrok (développement):**
   ```bash
   ngrok http 8000
   ```
   Utilisez l'URL ngrok (ex: `https://abc123.ngrok.io`) comme `APP_DOMAIN`

2. **Utiliser Cloudflare Tunnel:**
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```

3. **Utiliser un vrai domaine (production):**
   - Configurez votre domaine DNS pour pointer vers votre application
   - Utilisez ce domaine comme `APP_DOMAIN`

---

### ❌ Erreur de contrainte unique lors de la synchronisation

**Symptôme:**
```json
{
  "error": "duplicate key value violates unique constraint \"unique_vehicle_per_account\""
}
```

**Solution:**

Cette erreur a été corrigée. Le code vérifie maintenant si le véhicule existe avant d'insérer, et fait un UPDATE si nécessaire.

Si vous rencontrez encore cette erreur :
1. Vérifiez que vous utilisez la dernière version du code
2. Les véhicules existants seront automatiquement mis à jour

---

### ❌ Token Tesla utilisateur non trouvé

**Symptôme:**
```json
{
  "detail": "Token Tesla utilisateur non trouvé..."
}
```

**Solution:**

1. **Compléter le flux OAuth Tesla:**
   ```bash
   # 1. Démarrer le flux OAuth
   GET /api/auth/login
   
   # 2. Compléter l'authentification dans le navigateur
   
   # 3. Le token sera automatiquement lié lors de votre première requête authentifiée
   ```

2. **Vérifier l'état:**
   ```bash
   GET /api/auth/debug
   # Avec votre token Supabase
   ```

---

## Vérification de la configuration

### Endpoint de diagnostic

Utilisez `/api/fleet/partner/token-debug` pour diagnostiquer les problèmes de token partenaire :

```bash
curl -X 'GET' 'https://votre-domaine.com/api/fleet/partner/token-debug'
```

**Réponse attendue (succès):**
```json
{
  "access_token_preview": "eyJhbGciOiJS...",
  "audience": "https://fleet-api.prd.eu.vn.cloud.tesla.com",
  "auth_base": "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3",
  "scopes": "...",
  "expires_in": 28800,
  "token_type": "Bearer",
  "source": "cache" ou "fresh"
}
```

**Réponse en cas d'erreur:**
```json
{
  "error": "Tesla a refusé les credentials partenaires (403 Forbidden)...",
  "tesla_client_id_set": true,
  "tesla_client_secret_set": true,
  "auth_base": "...",
  "audience": "..."
}
```

---

## Checklist de configuration

Avant d'utiliser les endpoints partenaires, vérifiez :

- [ ] `TESLA_CLIENT_ID` est configuré et correct
- [ ] `TESLA_CLIENT_SECRET` est configuré et correct
- [ ] `TESLA_REGION` correspond à la région de vos credentials
- [ ] L'application existe dans le portail Tesla Developer
- [ ] Les permissions partenaire sont activées dans le portail
- [ ] `APP_DOMAIN` est un vrai domaine (pas localhost)
- [ ] `PUBLIC_KEY_URL` pointe vers votre clé publique (si nécessaire)

---

## Support

Si les problèmes persistent :

1. Vérifiez les logs de l'application dans DigitalOcean App Platform
2. Utilisez `/api/fleet/partner/token-debug` pour diagnostiquer
3. Vérifiez la configuration dans le portail Tesla Developer
4. Assurez-vous que vous utilisez les bons credentials pour le bon environnement

