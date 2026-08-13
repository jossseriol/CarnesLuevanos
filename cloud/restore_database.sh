#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Uso: ./restore_database.sh backups/database_YYYYMMDD_HHMMSS.db"
  exit 1
fi

BACKUP="$1"
if [ ! -f "$BACKUP" ]; then
  echo "No existe el respaldo: $BACKUP"
  exit 1
fi

API_CONTAINER="$(docker compose ps -q api)"
if [ -z "$API_CONTAINER" ]; then
  echo "No se encontro el contenedor api."
  exit 1
fi

docker compose stop api
docker cp "$BACKUP" "$API_CONTAINER:/app/data/database.db"
docker compose start api
echo "Base restaurada desde: $BACKUP"
