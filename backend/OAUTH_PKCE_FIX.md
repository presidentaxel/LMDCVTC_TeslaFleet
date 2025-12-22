# Fix pour les problèmes OAuth PKCE

## Problèmes identifiés

### 1. ❌ Erreur 403 "Access Denied" d'Akamai
**Symptôme** : `You don't have permission to access "http://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token"`

**Cause** : L'IP de DigitalOcean est bloquée par le CDN/firewall de Tesla (Akamai).

**Solutions** :
- ✅ Le code utilise maintenant l'issuer correct du callback
- ✅ Headers HTTP améliorés (User-Agent, etc.)
- ⚠️ **Action requise** : Contacter Tesla Support pour débloquer votre IP DigitalOcean

### 2. ❌ PKCE verifier introuvable
**Symptôme** : `PKCE verifier introuvable (state expiré ou invalide)`

**Causes possibles** :
1. Le verifier n'est pas stocké correctement dans Supabase
2. Le verifier est stocké mais pas récupéré (problème de clé ou format)
3. Le state ne correspond pas entre le login et le callback
4. Environnement multi-instances où le verifier est stocké sur une instance et récupéré sur une autre

**Solutions appliquées** :
- ✅ Stockage du PKCE verifier dans Supabase (persistant)
- ✅ Fallback sur mémoire si Supabase échoue
- ✅ Logs détaillés pour déboguer
- ✅ Vérification immédiate après stockage

## Vérifications à faire

### 1. Vérifier que TOKEN_STORE_TYPE est configuré
```bash
TOKEN_STORE_TYPE=supabase
```

### 2. Vérifier que Supabase est accessible
Les logs devraient montrer :
- `✅ PKCE verifier stocké dans Supabase pour state: ...`
- `✅ Vérification: PKCE verifier correctement stocké et récupérable`

### 3. Vérifier les logs lors du callback
Les logs devraient montrer :
- `Tentative de récupération du PKCE verifier depuis Supabase pour state: ...`
- `Données récupérées depuis Supabase: True`
- `PKCE verifier trouvé dans Supabase: True`

## Flux OAuth attendu

1. **Frontend appelle** `/api/auth/authorize-url` ou `/api/auth/login`
   - Génère un `state` unique
   - Génère un `code_verifier` PKCE
   - Stocke le verifier dans Supabase avec la clé `pkce_verifier:{state}`
   - Retourne l'URL d'autorisation Tesla avec le `state` et `code_challenge`

2. **Utilisateur redirigé vers Tesla**
   - Tesla authentifie l'utilisateur
   - Tesla redirige vers `/api/auth/callback?code=...&state=...&issuer=...`

3. **Backend reçoit le callback**
   - Récupère le `state` et le `code`
   - Récupère le `code_verifier` depuis Supabase avec la clé `pkce_verifier:{state}`
   - Échange le code contre un token en utilisant le verifier
   - Supprime le verifier (one-time use)

## Problème de blocage IP

L'erreur "Access Denied" d'Akamai indique que l'IP de DigitalOcean est bloquée. C'est un problème réseau, pas de code.

**Actions à prendre** :
1. Contacter Tesla Support pour débloquer votre IP
2. Vérifier que votre domaine est bien enregistré dans le portail Tesla
3. Essayer depuis une autre IP/réseau pour confirmer

## Logs à surveiller

Après déploiement, surveillez les logs pour :
- ✅ `PKCE verifier stocké dans Supabase` - Confirme le stockage
- ✅ `PKCE verifier trouvé dans Supabase` - Confirme la récupération
- ❌ `PKCE verifier non trouvé dans Supabase` - Indique un problème de stockage/récupération
- ❌ `Erreur lors de la récupération du PKCE verifier` - Indique un problème Supabase

