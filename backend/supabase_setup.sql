-- Script SQL pour créer la table tokens dans Supabase
-- À exécuter dans l'éditeur SQL de Supabase

-- Créer la table tokens
CREATE TABLE IF NOT EXISTS tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key TEXT UNIQUE NOT NULL,
  token_data JSONB NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour les recherches rapides
CREATE INDEX IF NOT EXISTS idx_tokens_key ON tokens(key);
CREATE INDEX IF NOT EXISTS idx_tokens_expires_at ON tokens(expires_at);

-- Fonction pour nettoyer automatiquement les tokens expirés
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
  DELETE FROM tokens WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Optionnel: Créer un trigger pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_tokens_updated_at
  BEFORE UPDATE ON tokens
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) - Optionnel mais recommandé
-- Activer RLS
ALTER TABLE tokens ENABLE ROW LEVEL SECURITY;

-- Politique: Permettre les opérations via l'API (service role key)
-- Note: Ajustez selon vos besoins de sécurité
CREATE POLICY "Allow service role full access"
  ON tokens
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- Ou si vous voulez plus de sécurité, utilisez une politique basée sur l'authentification
-- CREATE POLICY "Allow authenticated access"
--   ON tokens
--   FOR ALL
--   USING (auth.role() = 'service_role');

