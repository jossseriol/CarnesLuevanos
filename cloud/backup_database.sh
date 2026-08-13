#!/usr/bin/env bash
set -euo pipefail

mkdir -p backups
STAMP="$(date +%Y%m%d_%H%M%S)"
API_CONTAINER="$(docker compose ps -q api)"

if [ -z "$API_CONTAINER" ]; then
  echo "No se encontro el contenedor api."
  exit 1
fi

docker cp "$API_CONTAINER:/app/data/database.db" "backups/database_$STAMP.db"
echo "Respaldo creado: backups/database_$STAMP.db"
