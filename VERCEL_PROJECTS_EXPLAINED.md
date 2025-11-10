# 📦 Explication des projets Vercel

## Deux projets Vercel distincts

Tu as besoin de **2 projets Vercel différents** dans ton compte, mais ils servent des objectifs complètement différents :

### 1. `public-key-site` (Déjà fait ✅)
- **Rôle** : Servir uniquement la clé publique Tesla (fichier `.pem`)
- **URL** : `https://public-key-site.vercel.app`
- **Contenu** : Juste un fichier statique
- **Utilisé par** : Tesla pour vérifier ton domaine partenaire
- **Dossier** : `apps/public-key-site`

### 2. `web-frontend` (À créer 🆕)
- **Rôle** : Application React complète avec page d'authentification
- **URL** : `https://ton-app.vercel.app` (ou un autre nom)
- **Contenu** : Interface utilisateur complète (auth, véhicules, etc.)
- **Utilisé par** : Les utilisateurs finaux pour se connecter
- **Dossier** : `apps/web-frontend`

## 🎯 Pourquoi deux projets ?

| Aspect | public-key-site | web-frontend |
|--------|----------------|--------------|
| **Taille** | ~1 fichier | Application React complète |
| **Fréquence de mise à jour** | Rare (juste la clé) | Fréquente (features, UI) |
| **Domaine** | `public-key-site.vercel.app` | `ton-app.vercel.app` |
| **Build** | Aucun (statique) | `npm run build` |
| **Dépendances** | Aucune | React, Vite, etc. |

## 📋 Comment créer le 2ème projet Vercel

### Option 1 : Nouveau projet dans le même compte (Recommandé)

1. **Va sur Vercel Dashboard**
   - https://vercel.com/dashboard

2. **Clique sur "Add New Project"**

3. **Importe le même repo GitHub**
   - Sélectionne ton repo `tesla-fleet`

4. **Configure le projet**
   - **Project Name** : `tesla-fleet-frontend` (ou autre nom)
   - **Root Directory** : `apps/web-frontend` ⚠️ (IMPORTANT : différent du premier projet)
   - **Framework Preset** : Vite (ou détecté automatiquement)
   - **Build Command** : `npm run build`
   - **Output Directory** : `dist`

5. **Variables d'environnement**
   ```
   VITE_API_BASE=https://ton-backend.railway.app/api
   ```

6. **Déploie**
   - Vercel te donne une URL : `https://tesla-fleet-frontend.vercel.app`

### Option 2 : Utiliser le même domaine (Avancé)

Si tu veux utiliser le même domaine pour les deux :
- Configure un sous-domaine : `app.public-key-site.vercel.app`
- Ou utilise un domaine personnalisé avec routing

Mais c'est plus complexe et pas nécessaire.

## 🔗 Résumé des URLs

Après déploiement, tu auras :

1. **Clé publique** : `https://public-key-site.vercel.app`
   - Fichier : `/.well-known/appspecific/com.tesla.3p.public-key.pem`
   - Utilisé par : Tesla (enregistrement partenaire)

2. **Frontend app** : `https://tesla-fleet-frontend.vercel.app`
   - Page auth : `/auth`
   - Utilisé par : Les utilisateurs finaux

3. **Backend API** : `https://ton-backend.railway.app`
   - Endpoints : `/api/*`
   - Utilisé par : Le frontend

## ✅ Configuration finale

### Backend (.env ou Railway)
```
APP_DOMAIN=public-key-site.vercel.app  # Le site de la clé publique
PUBLIC_KEY_URL=https://public-key-site.vercel.app/.well-known/appspecific/com.tesla.3p.public-key.pem
FRONTEND_URL=https://tesla-fleet-frontend.vercel.app  # Le frontend React
CORS_ORIGINS=https://tesla-fleet-frontend.vercel.app
TP_REDIRECT_URI=https://ton-backend.railway.app/api/auth/callback
```

### Frontend (Vercel env vars)
```
VITE_API_BASE=https://ton-backend.railway.app/api
```

## 💡 Pourquoi pas un seul projet ?

Tu **pourrais** techniquement servir les deux depuis un seul projet Vercel, mais :
- ❌ Plus complexe à configurer
- ❌ Mélange deux objectifs différents
- ❌ Plus difficile à maintenir
- ✅ **Deux projets = plus simple et plus clair**

## 🎯 En résumé

- ✅ **public-key-site** : Déjà fait, ne touche pas
- 🆕 **web-frontend** : Nouveau projet Vercel, même repo, dossier différent
- 🔗 Les deux peuvent coexister sans problème

