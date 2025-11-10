# 🚀 Guide de déploiement gratuit et sécurisé

## Options gratuites recommandées

### 1. **Vercel** (Recommandé pour le frontend) ⭐
- ✅ Gratuit, très rapide
- ✅ HTTPS automatique
- ✅ Déploiement en 2 minutes
- ✅ Parfait pour React/Vite

### 2. **Railway** (Recommandé pour le backend) ⭐
- ✅ Gratuit avec crédits mensuels ($5 gratuits/mois)
- ✅ Supporte Python/FastAPI
- ✅ Variables d'environnement sécurisées
- ✅ HTTPS automatique

### 3. **Render** (Alternative)
- ✅ Gratuit avec limitations
- ✅ Supporte Python/FastAPI
- ✅ HTTPS automatique

## 📋 Déploiement étape par étape

### Frontend (Vercel) - 5 minutes

> **⚠️ Important** : Si tu as déjà un projet Vercel pour `public-key-site`, crée un **NOUVEAU projet** pour le frontend. Ce sont deux projets distincts dans le même compte Vercel.

1. **Préparer le projet**
   ```bash
   cd apps/web-frontend
   npm run build
   ```

2. **Créer un NOUVEAU projet Vercel**
   - Va sur https://vercel.com/dashboard
   - Clique sur "Add New Project" (même si tu as déjà `public-key-site`)
   - Importe le **même repo GitHub** (ton repo `tesla-fleet`)

3. **Configurer le projet**
   - **Project Name** : `tesla-fleet-frontend` (ou autre nom)
   - **Root Directory** : `apps/web-frontend` ⚠️ (IMPORTANT : différent de `public-key-site`)
   - **Framework Preset** : Vite (détecté automatiquement)
   - **Build Command** : `npm run build`
   - **Output Directory** : `dist`
   - **Environment Variables**:
     ```
     VITE_API_BASE=https://ton-backend.railway.app/api
     ```

4. **Récupérer l'URL**
   - Vercel te donne une URL : `https://tesla-fleet-frontend.vercel.app`
   - Note cette URL pour la config backend
   - ⚠️ C'est une URL **différente** de `public-key-site.vercel.app`

### Backend (Railway) - 10 minutes

1. **Créer un compte Railway**
   - Va sur https://railway.app
   - Connecte-toi avec GitHub

2. **Créer un nouveau projet**
   - "New Project" → "Deploy from GitHub repo"
   - Sélectionne ton repo

3. **Configurer le service**
   - Root Directory: `apps/api-backend`
   - Build Command: (vide, Railway détecte automatiquement)
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Variables d'environnement**
   - Clique sur "Variables"
   - Ajoute toutes tes variables `.env` :
     ```
     TESLA_CLIENT_ID=...
     TESLA_CLIENT_SECRET=...
     TP_CLIENT_ID=...
     TP_CLIENT_SECRET=...
     TP_REDIRECT_URI=https://ton-backend.railway.app/api/auth/callback
     FRONTEND_URL=https://ton-app.vercel.app
     CORS_ORIGINS=https://ton-app.vercel.app,https://ton-app-git-main.vercel.app
     APP_DOMAIN=public-key-site.vercel.app
     PUBLIC_KEY_URL=https://public-key-site.vercel.app/.well-known/appspecific/com.tesla.3p.public-key.pem
     REDIS_URL=redis://... (Railway peut créer un Redis gratuit)
     ```

5. **Récupérer l'URL**
   - Railway te donne une URL : `https://ton-backend.railway.app`
   - Note cette URL

6. **Mettre à jour le portail Tesla**
   - Va sur https://developer.tesla.com
   - Modifie ton OAuth client :
     - Redirect URI: `https://ton-backend.railway.app/api/auth/callback`
   - Sauvegarde

### Mise à jour des URLs

1. **Backend (.env ou Railway variables)**
   ```
   TP_REDIRECT_URI=https://ton-backend.railway.app/api/auth/callback
   FRONTEND_URL=https://ton-app.vercel.app
   CORS_ORIGINS=https://ton-app.vercel.app
   ```

2. **Frontend (Vercel environment variables)**
   ```
   VITE_API_BASE=https://ton-backend.railway.app/api
   ```

3. **Redéployer**
   - Frontend: Vercel redéploie automatiquement
   - Backend: Railway redéploie automatiquement

## 🔒 Sécurité

### ✅ Bonnes pratiques

1. **Variables d'environnement**
   - Ne jamais commiter les secrets
   - Utiliser les variables d'environnement des plateformes

2. **HTTPS**
   - Automatique sur Vercel et Railway
   - Pas de configuration nécessaire

3. **CORS**
   - Limiter aux domaines autorisés uniquement
   - Ne pas utiliser `*` en production

4. **Secrets Tesla**
   - Stocker dans les variables d'environnement
   - Ne jamais les exposer dans le code

## 🆓 Limites gratuites

### Vercel
- ✅ Illimité pour usage personnel
- ✅ 100GB bandwidth/mois
- ✅ Parfait pour un one-time

### Railway
- ✅ $5 gratuits/mois
- ✅ ~500 heures de runtime/mois
- ✅ Suffisant pour un usage ponctuel

## 🚨 Alternative : Render (100% gratuit)

Si Railway ne suffit pas :

1. **Créer un compte Render**
   - https://render.com
   - Connecte-toi avec GitHub

2. **Déployer le backend**
   - "New" → "Web Service"
   - Connecte ton repo
   - Root Directory: `apps/api-backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment Variables: (même que Railway)

3. **Limitations Render**
   - ⚠️ Le service s'endort après 15 min d'inactivité
   - ⚠️ Premier démarrage peut être lent (~30s)
   - ✅ Mais 100% gratuit

## 📝 Checklist de déploiement

- [ ] Frontend déployé sur Vercel
- [ ] Backend déployé sur Railway/Render
- [ ] Variables d'environnement configurées
- [ ] URLs mises à jour dans le portail Tesla
- [ ] CORS configuré avec les bonnes origines
- [ ] Test de connexion OAuth fonctionnel
- [ ] HTTPS actif (automatique)

## 🎯 URLs finales

- Frontend: `https://ton-app.vercel.app`
- Backend: `https://ton-backend.railway.app`
- Page auth: `https://ton-app.vercel.app/auth`

## 💡 Tips

1. **Pour un one-time** : Vercel + Railway est parfait
2. **Pour tester** : Utilise les preview URLs de Vercel
3. **Pour la prod** : Configure un domaine personnalisé (optionnel)

## 🆘 Dépannage

**CORS errors ?**
- Vérifie que `CORS_ORIGINS` contient l'URL exacte du frontend
- Vérifie que le backend redémarre après changement

**OAuth ne fonctionne pas ?**
- Vérifie que `TP_REDIRECT_URI` correspond exactement à l'URL du callback
- Vérifie dans le portail Tesla que l'URL est bien enregistrée

**Backend ne démarre pas ?**
- Vérifie les logs Railway/Render
- Vérifie que toutes les variables d'environnement sont définies

