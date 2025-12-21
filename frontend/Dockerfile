# Stage 1: Build
FROM node:20-alpine AS build

WORKDIR /app

# Copier les fichiers de dépendances
COPY package*.json ./

# Installer les dépendances
RUN npm install

# Copier le code source
COPY . .

# Variables d'environnement pour le build (ARG pour build-time, ENV pour runtime)
ARG VITE_API_BASE=http://localhost:8000/api
ENV VITE_API_BASE=${VITE_API_BASE}

# Builder l'application
RUN npm run build

# Vérifier que le build a réussi
RUN test -d dist && echo "Build successful" || (echo "Build failed!" && exit 1)

# Stage 2: Production
FROM nginx:alpine

# Copier les fichiers buildés
COPY --from=build /app/dist /usr/share/nginx/html

# Vérifier que les fichiers sont présents
RUN ls -la /usr/share/nginx/html/ || echo "Warning: dist directory might be empty"

# Configuration nginx pour SPA
RUN cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;
    
    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Exposer le port
EXPOSE 80

# Commande par défaut
CMD ["nginx", "-g", "daemon off;"]
