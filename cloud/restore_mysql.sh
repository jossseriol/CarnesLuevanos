#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Uso: ./restore_mysql.sh respaldo.sql"
  exit 1
fi

if [ ! -f .env ]; then
  echo "No existe .env. Copia .env.mysql.example a .env y configura tus claves."
  exit 1
fi

set -a
source .env
set +a

docker compose -f docker-compose.mysql.yml --env-file .env exec -T mysql \
  mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" < "$1"

echo "Respaldo restaurado: $1"
