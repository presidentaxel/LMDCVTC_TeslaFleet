# 🚀 Migration vers Supabase - Résumé

## Pourquoi Redis était utilisé ?

Redis servait uniquement à **stocker et mettre en cache les tokens OAuth** :
- Tokens partenaires (M2M) pour les appels API Tesla
- Tokens utilisateurs (OAuth) pour les sessions
- Cache avec expiration automatique (TTL)

## Pourquoi Supabase est mieux ?

✅ **Base de données complète** : Plus qu'un simple cache  
✅ **Persistance** : Données sauvegardées  
✅ **Sécurité** : RLS, authentification intégrée  
✅ **Gratuit** : Plan gratuit généreux  
✅ **Pas de service supplémentaire** : Tout dans Supabase  
✅ **API simple** : Accès facile depuis le code Python

## Configuration rapide

### 1. Créer un projet Supabase
1. Allez sur [supabase.com](https://supabase.com)
2. Créez un projet
3. Récupérez votre URL et Service Role Key

### 2. Créer la table
Exécutez `backend/supabase_setup.sql` dans l'éditeur SQL de Supabase

### 3. Configurer `.env`
```env
TOKEN_STORE_TYPE=supabase
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre-service-role-key
```

### 4. Installer les dépendances
```bash
cd backend
pip install -r requirements.txt
```

C'est tout ! Le système bascule automatiquement vers Supabase.

## Architecture

```
┌─────────────┐
│   Backend   │
│   FastAPI   │
└──────┬──────┘
       │
       ├─► Redis (optionnel)
       │   └─► Cache tokens
       │
       └─► Supabase (recommandé)
           └─► Table tokens
               ├─► key (TEXT)
               ├─► token_data (JSONB)
               └─► expires_at (TIMESTAMPTZ)
```

## Fichiers créés

- `backend/app/auth/supabase_store.py` - Store Supabase
- `backend/app/auth/store_factory.py` - Factory pour choisir le store
- `backend/supabase_setup.sql` - Script SQL pour créer la table
- `SUPABASE_SETUP.md` - Guide complet
- `REDIS_EXPLANATION.md` - Explication de l'utilisation de Redis

## Compatibilité

Le code est **100% compatible** :
- ✅ Fonctionne avec Redis (existant)
- ✅ Fonctionne avec Supabase (nouveau)
- ✅ Fallback automatique en mémoire si les deux échouent

Aucun changement nécessaire dans le code existant !

