# Guide d'utilisation des tables multi-comptes Tesla

## Vue d'ensemble

Le système permet maintenant de :
1. **Gérer plusieurs comptes Tesla** par utilisateur Supabase
2. **Mettre en cache les données des véhicules** pour éviter les appels répétés à l'API Tesla
3. **Mettre en cache les réponses d'autres endpoints** (charge_state, vehicle_state, etc.)

## Structure des données

### 1. Comptes Tesla (`tesla_accounts`)

Chaque utilisateur Supabase peut avoir plusieurs comptes Tesla :

```sql
-- Créer un compte Tesla
INSERT INTO tesla_accounts (supabase_user_id, account_name, email)
VALUES ('user-uuid-from-supabase', 'Compte principal', 'user@example.com');

-- Lister les comptes d'un utilisateur
SELECT * FROM tesla_accounts WHERE supabase_user_id = 'user-uuid';
```

### 2. Tokens (`tokens` - modifiée)

Les tokens sont maintenant liés à un compte Tesla :

```sql
-- Le token est stocké avec tesla_account_id
-- Clé: user_token:{supabase_user_id}:{tesla_account_id}
-- Ou: user_token:{supabase_user_id} (pour rétrocompatibilité)
```

### 3. Véhicules (`vehicles`)

Cache des données des véhicules :

```sql
-- Insérer/mettre à jour un véhicule
INSERT INTO vehicles (
  tesla_account_id, tesla_id, tesla_vehicle_id, vin,
  vehicle_data, display_name, access_type, state, in_service, api_version
)
VALUES (
  'account-uuid', 1492932226450100, 999823797, '5YJ3E7EB8LF677109',
  '{"id": 1492932226450100, ...}'::jsonb,
  'Ma Tesla', 'OWNER', 'online', false, 87
)
ON CONFLICT (tesla_account_id, tesla_id)
DO UPDATE SET
  vehicle_data = EXCLUDED.vehicle_data,
  display_name = EXCLUDED.display_name,
  state = EXCLUDED.state,
  updated_at = NOW(),
  last_synced_at = NOW();

-- Récupérer tous les véhicules d'un compte
SELECT * FROM vehicles WHERE tesla_account_id = 'account-uuid';

-- Rechercher par VIN
SELECT * FROM vehicles WHERE vin = '5YJ3E7EB8LF677109';
```

### 4. Cache des données (`vehicle_data_cache`)

Cache des réponses d'autres endpoints :

```sql
-- Stocker une réponse d'endpoint
INSERT INTO vehicle_data_cache (
  tesla_account_id, vehicle_id, endpoint_name, response_data, expires_at
)
VALUES (
  'account-uuid', 'vehicle-uuid', 'charge_state',
  '{"battery_level": 80, ...}'::jsonb,
  NOW() + INTERVAL '5 minutes'
)
ON CONFLICT (vehicle_id, endpoint_name)
DO UPDATE SET
  response_data = EXCLUDED.response_data,
  expires_at = EXCLUDED.expires_at,
  updated_at = NOW(),
  last_fetched_at = NOW();

-- Récupérer le cache (si non expiré)
SELECT response_data FROM vehicle_data_cache
WHERE vehicle_id = 'vehicle-uuid'
  AND endpoint_name = 'charge_state'
  AND (expires_at IS NULL OR expires_at > NOW());
```

## Exemple d'utilisation en Python

```python
from supabase import create_client
from app.core.settings import settings

supabase = create_client(settings.SUPABASE_URL, settings.get_supabase_key_for_admin())

# 1. Créer un compte Tesla pour un utilisateur
def create_tesla_account(user_id: str, account_name: str, email: str = None):
    result = supabase.table('tesla_accounts').insert({
        'supabase_user_id': user_id,
        'account_name': account_name,
        'email': email,
        'is_active': True
    }).execute()
    return result.data[0]['id']

# 2. Stocker un token lié à un compte Tesla
def store_token_for_account(account_id: str, token_data: dict, ttl: int):
    key = f"user_token:{account_id}"
    expires_at = datetime.utcnow() + timedelta(seconds=ttl)
    
    supabase.table('tokens').upsert({
        'key': key,
        'token_data': token_data,
        'expires_at': expires_at.isoformat(),
        'tesla_account_id': account_id
    }).execute()

# 3. Mettre en cache les véhicules
def cache_vehicles(account_id: str, vehicles_data: list):
    for vehicle in vehicles_data:
        supabase.table('vehicles').upsert({
            'tesla_account_id': account_id,
            'tesla_id': vehicle['id'],
            'tesla_vehicle_id': vehicle['vehicle_id'],
            'vin': vehicle['vin'],
            'vehicle_data': vehicle,
            'display_name': vehicle.get('display_name'),
            'access_type': vehicle.get('access_type'),
            'state': vehicle.get('state'),
            'in_service': vehicle.get('in_service', False),
            'api_version': vehicle.get('api_version'),
            'last_synced_at': datetime.utcnow().isoformat()
        }).execute()

# 4. Récupérer les véhicules depuis le cache
def get_cached_vehicles(account_id: str, max_age_minutes: int = 5):
    cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
    
    result = supabase.table('vehicles')\
        .select('*')\
        .eq('tesla_account_id', account_id)\
        .gte('last_synced_at', cutoff_time.isoformat())\
        .execute()
    
    return result.data

# 5. Mettre en cache une réponse d'endpoint
def cache_endpoint_response(account_id: str, vehicle_id: str, endpoint_name: str, 
                          response_data: dict, ttl_minutes: int = 5):
    expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
    
    supabase.table('vehicle_data_cache').upsert({
        'tesla_account_id': account_id,
        'vehicle_id': vehicle_id,
        'endpoint_name': endpoint_name,
        'response_data': response_data,
        'expires_at': expires_at.isoformat(),
        'last_fetched_at': datetime.utcnow().isoformat()
    }).execute()

# 6. Récupérer depuis le cache
def get_cached_endpoint(vehicle_id: str, endpoint_name: str):
    result = supabase.table('vehicle_data_cache')\
        .select('response_data')\
        .eq('vehicle_id', vehicle_id)\
        .eq('endpoint_name', endpoint_name)\
        .gt('expires_at', datetime.utcnow().isoformat())\
        .execute()
    
    if result.data:
        return result.data[0]['response_data']
    return None
```

## Index de performance

Les index suivants ont été créés pour optimiser les performances :

### `tesla_accounts`
- `idx_tesla_accounts_user_id` : Recherche rapide par utilisateur
- `idx_tesla_accounts_active` : Filtrage des comptes actifs
- `idx_tesla_accounts_user_active` : Recherche combinée utilisateur + actif

### `vehicles`
- `idx_vehicles_tesla_account_id` : Recherche par compte Tesla
- `idx_vehicles_vin` : Recherche par VIN
- `idx_vehicles_tesla_id` : Recherche par ID Tesla
- `idx_vehicles_state` : Filtrage par état (online/offline/asleep)
- `idx_vehicles_account_state` : Recherche combinée compte + état
- `idx_vehicles_data_gin` : Recherche dans les données JSONB

### `vehicle_data_cache`
- `idx_cache_vehicle_id` : Recherche par véhicule
- `idx_cache_endpoint` : Recherche par endpoint
- `idx_cache_expires_at` : Nettoyage des entrées expirées
- `idx_cache_account_endpoint` : Recherche combinée compte + endpoint
- `idx_cache_data_gin` : Recherche dans les données JSONB

## Nettoyage automatique

Pour nettoyer le cache expiré, vous pouvez créer un job cron :

```sql
-- Exécuter périodiquement (ex: toutes les heures)
SELECT cleanup_expired_cache();
```

Ou via Supabase Edge Functions ou un cron job externe.

