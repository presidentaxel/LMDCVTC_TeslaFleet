# Structure de l'API FastAPI

L'API est organisée en sections claires pour faciliter la maintenance et la compréhension.

## Organisation des endpoints

### 📊 `/api/fleet/sync/*` - Endpoints SYNC (avec cache Supabase)

Ces endpoints vérifient d'abord le cache Supabase, puis synchronisent avec Tesla si nécessaire.

**Fichier:** `backend/app/api/routes_fleet_sync.py`

- `GET /api/fleet/sync/vehicles` - Liste des véhicules (cache + sync auto)
- `GET /api/fleet/sync/vehicles/{vehicle_id}/data/{endpoint_name}` - Données d'un endpoint (cache + sync auto)
- `POST /api/fleet/sync/sync` - Synchroniser tous les véhicules avec Tesla

**Caractéristiques:**
- ✅ Utilise le cache Supabase en priorité
- ✅ Synchronise automatiquement si le cache est expiré
- ✅ Paramètre `force_refresh` pour forcer la synchronisation
- ✅ Paramètre `max_cache_age_minutes` pour contrôler la validité du cache

**Exemple:**
```bash
# Récupérer les véhicules (depuis le cache si disponible)
GET /api/fleet/sync/vehicles

# Forcer la synchronisation avec Tesla
GET /api/fleet/sync/vehicles?force_refresh=true

# Récupérer les données de charge (depuis le cache si disponible)
GET /api/fleet/sync/vehicles/1492932226450100/data/charge_state
```

---

### 🗄️ `/api/fleet/supabase/*` - Endpoints SUPABASE (cache uniquement)

Ces endpoints récupèrent les données depuis Supabase uniquement, sans appeler Tesla.

**Fichier:** `backend/app/api/routes_fleet_supabase.py`

- `GET /api/fleet/supabase/vehicles` - Liste des véhicules depuis Supabase
- `GET /api/fleet/supabase/vehicles/{vehicle_id}/data/{endpoint_name}` - Données d'un endpoint depuis Supabase
- `GET /api/fleet/supabase/accounts` - Liste des comptes Tesla

**Caractéristiques:**
- ✅ Accès direct à Supabase uniquement
- ✅ Pas d'appel à l'API Tesla
- ✅ Retourne une erreur si les données ne sont pas en cache
- ✅ Idéal pour les tableaux de bord et les requêtes fréquentes

**Exemple:**
```bash
# Récupérer les véhicules depuis Supabase uniquement
GET /api/fleet/supabase/vehicles

# Filtrer par état
GET /api/fleet/supabase/vehicles?state=online

# Récupérer les données de charge depuis Supabase
GET /api/fleet/supabase/vehicles/1492932226450100/data/charge_state
```

---

### ⚡ `/api/fleet/direct/*` - Endpoints DIRECT (appels Tesla en temps réel)

Ces endpoints font des appels directs à l'API Tesla sans utiliser le cache.

**Fichier:** `backend/app/api/routes_fleet_direct.py`

- `POST /api/fleet/direct/vehicles/{vehicle_id}/wake` - Réveiller un véhicule
- `POST /api/fleet/direct/vehicles/{vehicle_id}/lock` - Verrouiller un véhicule
- `POST /api/fleet/direct/vehicles/{vehicle_id}/unlock` - Déverrouiller un véhicule
- `POST /api/fleet/direct/vehicles/{vehicle_id}/charge/start` - Démarrer la charge
- `POST /api/fleet/direct/vehicles/{vehicle_id}/charge/stop` - Arrêter la charge
- `POST /api/fleet/direct/proxy` - Proxy générique vers l'API Tesla

**Caractéristiques:**
- ✅ Appels directs à Tesla (pas de cache)
- ✅ Réponses en temps réel
- ✅ Nécessaires pour les actions (wake, lock, unlock, charge)
- ✅ Proxy pour accéder à n'importe quel endpoint Tesla

**Exemple:**
```bash
# Réveiller un véhicule
POST /api/fleet/direct/vehicles/1492932226450100/wake

# Verrouiller un véhicule
POST /api/fleet/direct/vehicles/1492932226450100/lock

# Appel proxy générique
POST /api/fleet/direct/proxy
{
  "method": "GET",
  "path": "/api/1/vehicles/1492932226450100/vehicle_data",
  "region": "eu"
}
```

---

### 🔧 `/api/fleet/*` - Endpoints généraux et partenaire

Endpoints généraux et spécifiques au mode partenaire (M2M).

**Fichier:** `backend/app/api/routes_fleet.py`

- `GET /api/fleet/status` - Statut de l'API Fleet (partenaire)
- `GET /api/fleet/partner/telemetry-errors` - Erreurs de télémétrie partenaire
- `GET /api/fleet/partner/token-debug` - Debug du token partenaire
- `POST /api/fleet/partner/register` - Enregistrer le domaine partenaire
- `GET /api/fleet/partner/public-key` - Clé publique partenaire

**Caractéristiques:**
- ✅ Endpoints spécifiques au mode partenaire (M2M)
- ✅ Utilisent les tokens partenaires (client_credentials)
- ✅ Ne nécessitent pas d'authentification utilisateur Supabase

---

## Service de cache

**Fichier:** `backend/app/services/vehicle_cache.py`

Le service `VehicleCacheService` gère toutes les opérations de cache :

- `get_active_tesla_account()` - Récupère le compte Tesla actif
- `create_or_get_tesla_account()` - Crée ou récupère un compte Tesla
- `cache_vehicles()` - Met en cache les véhicules
- `get_cached_vehicles()` - Récupère les véhicules depuis le cache
- `cache_endpoint_response()` - Met en cache une réponse d'endpoint
- `get_cached_endpoint()` - Récupère une réponse d'endpoint depuis le cache

---

## Flux recommandé

### 1. Synchronisation initiale
```bash
# Synchroniser tous les véhicules avec Tesla
POST /api/fleet/sync/sync
```

### 2. Récupération des données (avec cache automatique)
```bash
# Récupérer les véhicules (utilise le cache si disponible)
GET /api/fleet/sync/vehicles

# Récupérer les données de charge (utilise le cache si disponible)
GET /api/fleet/sync/vehicles/{vehicle_id}/data/charge_state
```

### 3. Accès rapide au cache (sans appel Tesla)
```bash
# Récupérer les véhicules depuis Supabase uniquement
GET /api/fleet/supabase/vehicles

# Récupérer les données depuis Supabase uniquement
GET /api/fleet/supabase/vehicles/{vehicle_id}/data/charge_state
```

### 4. Actions en temps réel
```bash
# Réveiller un véhicule (appel direct à Tesla)
POST /api/fleet/direct/vehicles/{vehicle_id}/wake

# Verrouiller un véhicule (appel direct à Tesla)
POST /api/fleet/direct/vehicles/{vehicle_id}/lock
```

---

## Avantages de cette organisation

1. **Clarté** : Chaque type d'endpoint a son propre préfixe et fichier
2. **Performance** : Les endpoints sync utilisent le cache pour réduire les appels à Tesla
3. **Flexibilité** : Les endpoints direct permettent les actions en temps réel
4. **Maintenabilité** : Code organisé et facile à comprendre
5. **Scalabilité** : Le cache Supabase permet de gérer plusieurs comptes Tesla par utilisateur

