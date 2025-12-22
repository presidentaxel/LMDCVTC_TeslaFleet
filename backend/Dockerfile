FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système si nécessaire (incluant curl pour health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Exposer le port (DigitalOcean injecte généralement PORT=8080)
EXPOSE 8000

# Commande par défaut (utilise PORT si défini, sinon 8000)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

