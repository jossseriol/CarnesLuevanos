#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"

if [ ! -f .env ]; then
  echo "No existe .env. Copia .env.mysql.example a .env y configura tus claves."
  exit 1
fi

set -a
source .env
set +a

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/carnes_luevanos_mysql_$STAMP.sql"

docker compose -f docker-compose.mysql.yml --env-file .env exec -T mysql \
  mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" > "$OUT"

echo "Respaldo creado: $OUT"
