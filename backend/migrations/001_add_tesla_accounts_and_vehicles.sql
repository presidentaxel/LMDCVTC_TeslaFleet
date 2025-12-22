-- Migration: Ajout de la gestion multi-comptes Tesla et cache des véhicules
-- À exécuter dans l'éditeur SQL de Supabase

-- ============================================================================
-- 1. Table tesla_accounts : Gérer plusieurs comptes Tesla par utilisateur
-- ============================================================================
CREATE TABLE IF NOT EXISTS tesla_accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  supabase_user_id TEXT NOT NULL, -- ID utilisateur Supabase (sub du JWT)
  account_name TEXT, -- Nom donné par l'utilisateur (ex: "Compte principal", "Compte flotte")
  email TEXT, -- Email du compte Tesla (optionnel, pour référence)
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Contrainte: un utilisateur peut avoir plusieurs comptes
  CONSTRAINT unique_account_per_user UNIQUE NULLS NOT DISTINCT (supabase_user_id, account_name)
);

-- Index pour les recherches rapides
CREATE INDEX IF NOT EXISTS idx_tesla_accounts_user_id ON tesla_accounts(supabase_user_id);
CREATE INDEX IF NOT EXISTS idx_tesla_accounts_active ON tesla_accounts(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_tesla_accounts_user_active ON tesla_accounts(supabase_user_id, is_active);

-- ============================================================================
-- 2. Modification de la table tokens pour lier aux comptes Tesla
-- ============================================================================
-- Ajouter la colonne tesla_account_id (nullable pour rétrocompatibilité)
ALTER TABLE tokens ADD COLUMN IF NOT EXISTS tesla_account_id UUID REFERENCES tesla_accounts(id) ON DELETE CASCADE;

-- Index pour les recherches par compte Tesla
CREATE INDEX IF NOT EXISTS idx_tokens_tesla_account_id ON tokens(tesla_account_id);
CREATE INDEX IF NOT EXISTS idx_tokens_key_account ON tokens(key, tesla_account_id);

-- ============================================================================
-- 3. Table vehicles : Cache des données des véhicules
-- ============================================================================
CREATE TABLE IF NOT EXISTS vehicles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tesla_account_id UUID NOT NULL REFERENCES tesla_accounts(id) ON DELETE CASCADE,
  
  -- Identifiants Tesla
  tesla_id BIGINT NOT NULL, -- ID Tesla (ex: 1492932226450100)
  tesla_vehicle_id BIGINT NOT NULL, -- vehicle_id Tesla (ex: 999823797)
  vin TEXT NOT NULL, -- VIN du véhicule
  
  -- Données du véhicule (stockées en JSONB pour flexibilité)
  vehicle_data JSONB NOT NULL, -- Toutes les données du véhicule
  
  -- Champs extraits pour faciliter les requêtes
  display_name TEXT,
  access_type TEXT, -- OWNER, DRIVER, etc.
  state TEXT, -- online, offline, asleep
  in_service BOOLEAN,
  api_version INTEGER,
  
  -- Métadonnées
  last_synced_at TIMESTAMPTZ DEFAULT NOW(), -- Dernière synchronisation avec Tesla
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Contrainte: un véhicule unique par compte Tesla
  CONSTRAINT unique_vehicle_per_account UNIQUE (tesla_account_id, tesla_id)
);

-- Index pour les performances
CREATE INDEX IF NOT EXISTS idx_vehicles_tesla_account_id ON vehicles(tesla_account_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_vin ON vehicles(vin);
CREATE INDEX IF NOT EXISTS idx_vehicles_tesla_id ON vehicles(tesla_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_state ON vehicles(state);
CREATE INDEX IF NOT EXISTS idx_vehicles_access_type ON vehicles(access_type);
CREATE INDEX IF NOT EXISTS idx_vehicles_last_synced ON vehicles(last_synced_at);
CREATE INDEX IF NOT EXISTS idx_vehicles_account_state ON vehicles(tesla_account_id, state);

-- Index GIN pour les recherches dans JSONB
CREATE INDEX IF NOT EXISTS idx_vehicles_data_gin ON vehicles USING GIN (vehicle_data);

-- ============================================================================
-- 4. Table vehicle_data_cache : Cache des réponses d'autres endpoints Tesla
-- ============================================================================
CREATE TABLE IF NOT EXISTS vehicle_data_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tesla_account_id UUID NOT NULL REFERENCES tesla_accounts(id) ON DELETE CASCADE,
  vehicle_id UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
  
  -- Identifiant de l'endpoint (ex: "charge_state", "vehicle_state", "climate_state")
  endpoint_name TEXT NOT NULL,
  
  -- Données de la réponse (stockées en JSONB)
  response_data JSONB NOT NULL,
  
  -- Métadonnées
  expires_at TIMESTAMPTZ, -- Optionnel: expiration du cache
  last_fetched_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Contrainte: une seule entrée par véhicule/endpoint
  CONSTRAINT unique_cache_entry UNIQUE (vehicle_id, endpoint_name)
);

-- Index pour les performances
CREATE INDEX IF NOT EXISTS idx_cache_tesla_account_id ON vehicle_data_cache(tesla_account_id);
CREATE INDEX IF NOT EXISTS idx_cache_vehicle_id ON vehicle_data_cache(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_cache_endpoint ON vehicle_data_cache(endpoint_name);
CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON vehicle_data_cache(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_cache_account_endpoint ON vehicle_data_cache(tesla_account_id, endpoint_name);

-- Index GIN pour les recherches dans JSONB
CREATE INDEX IF NOT EXISTS idx_cache_data_gin ON vehicle_data_cache USING GIN (response_data);

-- ============================================================================
-- 5. Triggers pour updated_at automatique
-- ============================================================================
-- Fonction pour mettre à jour updated_at (déjà créée, mais on l'utilise pour les nouvelles tables)
CREATE TRIGGER update_tesla_accounts_updated_at
  BEFORE UPDATE ON tesla_accounts
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vehicles_updated_at
  BEFORE UPDATE ON vehicles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vehicle_data_cache_updated_at
  BEFORE UPDATE ON vehicle_data_cache
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 6. Fonctions utilitaires
-- ============================================================================
-- Fonction pour nettoyer le cache expiré
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
  DELETE FROM vehicle_data_cache WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Fonction pour obtenir le compte Tesla actif d'un utilisateur
CREATE OR REPLACE FUNCTION get_active_tesla_account(p_user_id TEXT)
RETURNS UUID AS $$
DECLARE
  account_id UUID;
BEGIN
  SELECT id INTO account_id
  FROM tesla_accounts
  WHERE supabase_user_id = p_user_id AND is_active = true
  ORDER BY created_at ASC
  LIMIT 1;
  
  RETURN account_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 7. Row Level Security (RLS)
-- ============================================================================
-- Activer RLS sur les nouvelles tables
ALTER TABLE tesla_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE vehicles ENABLE ROW LEVEL SECURITY;
ALTER TABLE vehicle_data_cache ENABLE ROW LEVEL SECURITY;

-- Politiques pour tesla_accounts : les utilisateurs ne voient que leurs comptes
CREATE POLICY "Users can view their own tesla accounts"
  ON tesla_accounts
  FOR SELECT
  USING (auth.uid()::text = supabase_user_id OR auth.role() = 'service_role');

CREATE POLICY "Users can insert their own tesla accounts"
  ON tesla_accounts
  FOR INSERT
  WITH CHECK (auth.uid()::text = supabase_user_id OR auth.role() = 'service_role');

CREATE POLICY "Users can update their own tesla accounts"
  ON tesla_accounts
  FOR UPDATE
  USING (auth.uid()::text = supabase_user_id OR auth.role() = 'service_role');

CREATE POLICY "Users can delete their own tesla accounts"
  ON tesla_accounts
  FOR DELETE
  USING (auth.uid()::text = supabase_user_id OR auth.role() = 'service_role');

-- Politiques pour vehicles : les utilisateurs voient les véhicules de leurs comptes
CREATE POLICY "Users can view vehicles from their accounts"
  ON vehicles
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM tesla_accounts
      WHERE tesla_accounts.id = vehicles.tesla_account_id
      AND (tesla_accounts.supabase_user_id = auth.uid()::text OR auth.role() = 'service_role')
    )
  );

CREATE POLICY "Service role can manage vehicles"
  ON vehicles
  FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- Politiques pour vehicle_data_cache : même logique que vehicles
CREATE POLICY "Users can view cache from their accounts"
  ON vehicle_data_cache
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM vehicles
      JOIN tesla_accounts ON tesla_accounts.id = vehicles.tesla_account_id
      WHERE vehicles.id = vehicle_data_cache.vehicle_id
      AND (tesla_accounts.supabase_user_id = auth.uid()::text OR auth.role() = 'service_role')
    )
  );

CREATE POLICY "Service role can manage cache"
  ON vehicle_data_cache
  FOR ALL
  USING (auth.role() = 'service_role')
  WITH CHECK (auth.role() = 'service_role');

-- ============================================================================
-- 8. Migration des données existantes (si nécessaire)
-- ============================================================================
-- Créer un compte Tesla par défaut pour chaque utilisateur qui a déjà un token
-- Note: À exécuter manuellement après avoir vérifié les données existantes
/*
DO $$
DECLARE
  user_id_text TEXT;
  account_id UUID;
BEGIN
  -- Pour chaque token utilisateur existant, créer un compte Tesla par défaut
  FOR user_id_text IN 
    SELECT DISTINCT 
      SUBSTRING(key FROM 'user_token:(.*)') as user_id
    FROM tokens
    WHERE key LIKE 'user_token:%'
    AND SUBSTRING(key FROM 'user_token:(.*)') IS NOT NULL
  LOOP
    -- Créer un compte par défaut si n'existe pas déjà
    INSERT INTO tesla_accounts (supabase_user_id, account_name, is_active)
    VALUES (user_id_text, 'Compte principal', true)
    ON CONFLICT (supabase_user_id, account_name) DO NOTHING
    RETURNING id INTO account_id;
    
    -- Lier les tokens existants au compte (si account_id a été créé)
    IF account_id IS NOT NULL THEN
      UPDATE tokens
      SET tesla_account_id = account_id
      WHERE key = 'user_token:' || user_id_text
      AND tesla_account_id IS NULL;
    END IF;
  END LOOP;
END $$;
*/

