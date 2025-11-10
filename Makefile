make bootstrap          # installe deps, génère clé si absente (local)
make run                # docker-compose up -d
make register           # partner token + appel register par région
make test               # pytest -q && playwright test
make smoke              # curl /status && curl Tesla /status