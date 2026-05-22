# Guide d'authentification à distance

## 🎯 Objectif

Permettre à une personne distante de se connecter avec son compte Tesla et d'accorder les permissions nécessaires pour accéder à son véhicule.

## 🔒 Sécurité

- ✅ Flux OAuth 2.0 standard avec PKCE (Proof Key for Code Exchange)
- ✅ Aucun mot de passe stocké
- ✅ Tokens temporaires uniquement
- ✅ L'utilisateur peut révoquer l'accès à tout moment depuis son compte Tesla

## 📋 Utilisation

### Pour l'utilisateur distant

1. **Accéder à la page d'authentification**
   - Ouvrir l'URL : `http://localhost:8000/auth` (ou l'URL de production)
   - Ou partager le lien directement : `http://votre-domaine.com/auth`

2. **Se connecter**
   - Cliquer sur "Se connecter avec Tesla"
   - Être redirigé vers la page de connexion Tesla
   - Se connecter avec son compte Tesla
   - Accorder les permissions demandées

3. **Confirmation**
   - Après la connexion, l'utilisateur est automatiquement redirigé
   - Un message de confirmation s'affiche
   - Le token est maintenant actif et peut être utilisé pour accéder au véhicule

### Pour le développeur/admin

1. **Partager le lien**
   - Envoyer l'URL de la page d'authentification à la personne distante
   - Exemple : `https://votre-app.com/auth`

2. **Vérifier le statut**
   - Appeler `/api/auth/debug` pour vérifier si un token utilisateur est actif
   - Ou utiliser la page web qui affiche automatiquement le statut

3. **Utiliser les endpoints**
   - Une fois authentifié, tous les endpoints nécessitant un token utilisateur fonctionnent
   - Exemple : `/api/fleet/vehicles`, `/api/fleet/vehicles/{id}/command/...`

## 🌐 Déploiement

### En local
```bash
cd apps/web-frontend
npm run dev
```
Puis ouvrir : `http://localhost:5173/auth`

### En production
1. Configurer `VITE_API_BASE` dans les variables d'environnement
2. Builder l'application : `npm run build`
3. Déployer le dossier `dist/` sur votre serveur web

### Configuration backend

Assurez-vous que dans votre `.env` :
```
TP_CLIENT_ID=...
TP_CLIENT_SECRET=...
TP_REDIRECT_URI=http://localhost:8000/api/auth/callback  # ou votre URL de prod
TP_SCOPES=openid offline_access vehicle_device_data vehicle_cmds vehicle_charging_cmds
```

## 🔄 Flux OAuth

```
1. Utilisateur → /auth (page web)
2. Clic sur "Se connecter" → /api/auth/authorize-url
3. Redirection → Tesla OAuth (login + consentement)
4. Callback → /api/auth/callback?code=...&state=...
5. Backend échange code → token
6. Token stocké → utilisable pour les API
```

## ❓ FAQ

**Q: L'utilisateur peut-il se connecter plusieurs fois ?**  
R: Oui, chaque connexion remplace le token précédent.

**Q: Combien de temps le token est-il valide ?**  
R: Généralement 8 heures. Un refresh token permet de le renouveler automatiquement.

**Q: Comment révoquer l'accès ?**  
R: L'utilisateur peut révoquer l'accès depuis son compte Tesla → Applications connectées.

**Q: Plusieurs utilisateurs peuvent-ils se connecter ?**  
R: Actuellement, un seul token utilisateur est stocké. Pour plusieurs utilisateurs, il faudrait ajouter un système de sessions/DB.

## 🚀 Améliorations futures

- [ ] Support multi-utilisateurs avec sessions
- [ ] Interface pour gérer les tokens actifs
- [ ] Notifications lorsque le token expire
- [ ] Historique des connexions

