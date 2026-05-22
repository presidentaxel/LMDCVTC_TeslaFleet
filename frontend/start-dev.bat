@echo off
REM Script de démarrage pour le développement frontend (Windows)

echo 🚀 Démarrage du frontend en mode développement...

REM Vérifier si .env existe
if not exist .env (
    echo ⚠️  Fichier .env non trouvé, copie depuis env.example...
    copy env.example .env
    echo 📝 Veuillez éditer .env avec vos valeurs avant de continuer
)

REM Installer les dépendances si nécessaire
if not exist node_modules (
    echo 📦 Installation des dépendances...
    npm install
)

REM Lancer le serveur de développement
echo ✅ Démarrage du serveur (accessible depuis le réseau)
echo 📱 URL locale: http://localhost:5173
echo 🌐 URL réseau: http://[votre-ip]:5173
npm run dev

pause

