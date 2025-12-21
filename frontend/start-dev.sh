#!/bin/bash
# Script de démarrage pour le développement frontend

echo "🚀 Démarrage du frontend en mode développement..."

# Vérifier si .env existe
if [ ! -f ".env" ]; then
    echo "⚠️  Fichier .env non trouvé, copie depuis env.example..."
    cp env.example .env
    echo "📝 Veuillez éditer .env avec vos valeurs avant de continuer"
fi

# Installer les dépendances si nécessaire
if [ ! -d "node_modules" ]; then
    echo "📦 Installation des dépendances..."
    npm install
fi

# Lancer le serveur de développement
echo "✅ Démarrage du serveur (accessible depuis le réseau)"
echo "📱 URL locale: http://localhost:5173"
echo "🌐 URL réseau: http://[votre-ip]:5173"
npm run dev

