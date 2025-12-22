# Migrations Supabase

Ce dossier contient les migrations SQL pour la base de données Supabase.

## Installation

1. Connectez-vous à votre projet Supabase
2. Allez dans l'éditeur SQL
3. Exécutez les migrations dans l'ordre

## Ordre d'exécution

1. `001_add_tesla_accounts_and_vehicles.sql` - Ajoute la gestion multi-comptes Tesla et le cache des véhicules

## Structure des tables

### `tesla_accounts`
Gère plusieurs comptes Tesla par utilisateur Supabase.

### `tokens` (modifiée)
Ajout de la colonne `tesla_account_id` pour lier les tokens à un compte Tesla spécifique.

### `vehicles`
Cache des données des véhicules Tesla avec index optimisés.

### `vehicle_data_cache`
Cache des réponses d'autres endpoints Tesla (charge_state, vehicle_state, etc.).

## Migration des données existantes

Si vous avez déjà des tokens dans la table `tokens`, vous pouvez exécuter la section de migration des données à la fin du fichier `001_add_tesla_accounts_and_vehicles.sql` pour créer automatiquement un compte Tesla par défaut pour chaque utilisateur existant.

