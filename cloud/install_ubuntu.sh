#!/usr/bin/env bash
set -euo pipefail

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Edita cloud/.env antes de continuar:"
  echo "  DOMAIN=api.tudominio.com"
  echo "  API_SECRET_KEY=una-clave-larga-y-segura"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER" || true
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose no esta disponible. Cierra sesion y vuelve a entrar, o instala el plugin de compose."
  exit 1
fi

docker compose up -d --build
docker compose ps

echo ""
echo "API instalada. Prueba:"
echo "  curl https://$(grep '^DOMAIN=' .env | cut -d= -f2)/api/health"
