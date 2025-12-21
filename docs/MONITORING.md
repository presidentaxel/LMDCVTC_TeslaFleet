# 📊 Monitoring avec Prometheus et Grafana

Guide pour utiliser Prometheus et Grafana pour monitorer les performances de l'application Tesla Fleet.

## 🚀 Démarrage Rapide

### Avec Docker Compose

```bash
# Lancer tous les services avec monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Voir les logs
docker-compose -f docker-compose.monitoring.yml logs -f
```

### Accès aux Services

- **Grafana**: http://localhost:3000
  - Utilisateur: `admin`
  - Mot de passe: `admin` (à changer en production)
- **Prometheus**: http://localhost:9090
- **Backend API**: http://localhost:8000
- **Métriques Backend**: http://localhost:8000/metrics

## 📈 Métriques Disponibles

Le backend FastAPI expose automatiquement des métriques via `prometheus-fastapi-instrumentator`:

### Métriques HTTP
- `http_requests_total` - Nombre total de requêtes
- `http_request_duration_seconds` - Durée des requêtes
- `http_requests_in_progress` - Requêtes en cours
- `http_request_size_bytes` - Taille des requêtes
- `http_response_size_bytes` - Taille des réponses

### Métriques par endpoint
- Méthode HTTP (GET, POST, etc.)
- Code de statut (200, 404, 500, etc.)
- Endpoint (chemin de l'URL)

## 🎨 Dashboards Grafana

### Dashboard par défaut

Un dashboard de base est fourni dans `monitoring/grafana/dashboards/tesla-fleet-api.json` avec:
- Taux de requêtes par seconde
- Durée des requêtes (p95)
- Codes de statut HTTP
- Connexions actives
- Taux d'erreurs

### Créer un Dashboard Personnalisé

1. Accéder à Grafana: http://localhost:3000
2. Se connecter avec `admin/admin`
3. Aller dans **Dashboards** → **New Dashboard**
4. Ajouter des panels avec des requêtes PromQL

### Requêtes PromQL Utiles

```promql
# Taux de requêtes par seconde
rate(http_requests_total[5m])

# Durée moyenne des requêtes
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Taux d'erreurs (5xx)
rate(http_requests_total{status_code=~"5.."}[5m])

# Requêtes par endpoint
sum(rate(http_requests_total[5m])) by (endpoint)

# Latence p95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Latence p99
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

## 🔧 Configuration

### Prometheus

La configuration se trouve dans `monitoring/prometheus/prometheus.yml`.

Pour ajouter de nouvelles cibles:
```yaml
scrape_configs:
  - job_name: 'nouveau-service'
    static_configs:
      - targets: ['service:port']
```

### Grafana

Les datasources et dashboards sont provisionnés automatiquement via:
- `monitoring/grafana/provisioning/datasources/` - Sources de données
- `monitoring/grafana/provisioning/dashboards/` - Configuration des dashboards
- `monitoring/grafana/dashboards/` - Fichiers JSON des dashboards

## 🚨 Alertes (Optionnel)

Pour configurer des alertes dans Prometheus:

1. Créer `monitoring/prometheus/alert_rules.yml`
2. Décommenter la section `rule_files` dans `prometheus.yml`
3. Configurer Alertmanager (optionnel)

Exemple de règle d'alerte:
```yaml
groups:
  - name: tesla_fleet_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "Taux d'erreurs élevé"
```

## 📊 Métriques Personnalisées

Pour ajouter des métriques personnalisées dans le backend:

```python
from prometheus_client import Counter, Histogram

# Dans votre code
custom_counter = Counter('tesla_commands_total', 'Total Tesla commands', ['command_type'])
custom_histogram = Histogram('tesla_api_call_duration', 'Tesla API call duration', ['endpoint'])

# Utilisation
custom_counter.labels(command_type='wake_up').inc()
with custom_histogram.labels(endpoint='/vehicles').time():
    # Votre code ici
    pass
```

## 🔍 Debugging

### Vérifier que Prometheus scrape les métriques

1. Aller sur http://localhost:9090/targets
2. Vérifier que `tesla-fleet-backend` est "UP"

### Vérifier les métriques disponibles

1. Aller sur http://localhost:9090/graph
2. Taper `http_requests_total` dans la barre de recherche
3. Exécuter la requête

### Logs

```bash
# Logs Prometheus
docker logs prometheus

# Logs Grafana
docker logs grafana

# Logs Backend
docker logs backend
```

## 🛑 Arrêter les Services

```bash
docker-compose -f docker-compose.monitoring.yml down

# Supprimer aussi les volumes (perte de données)
docker-compose -f docker-compose.monitoring.yml down -v
```

## 🔐 Sécurité en Production

⚠️ **Important**: Les configurations par défaut ne sont pas sécurisées pour la production!

### Grafana
- Changer le mot de passe admin
- Configurer l'authentification (LDAP, OAuth, etc.)
- Activer HTTPS

### Prometheus
- Protéger l'accès avec un reverse proxy
- Configurer l'authentification
- Limiter l'accès réseau

## 📚 Ressources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus FastAPI Instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)

