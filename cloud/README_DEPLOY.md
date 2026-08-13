# Deploy profesional - Carnes Luevanos API

Arquitectura: API FastAPI en Docker + base SQLite persistente + Caddy con HTTPS automatico.

## Requisitos

- VPS Ubuntu 22.04/24.04
- Dominio o subdominio, por ejemplo `api.tudominio.com`
- DNS tipo A apuntando al IP publico del VPS
- Docker y Docker Compose instalados

## Instalacion en servidor

```bash
git clone TU_REPO CarnesLuevanos
cd CarnesLuevanos/cloud
cp .env.example .env
nano .env
chmod +x *.sh
./install_ubuntu.sh
```

Prueba:

```bash
curl https://api.tudominio.com/api/health
```

Debe responder:

```json
{"status":"ok"}
```

## Seguridad para Android/iOS

Configura `API_SECRET_KEY` en `.env`. Las apps deben enviar este header en cada peticion protegida:

```http
X-API-Key: TU_CLAVE_SEGURA
```

La ruta `/api/health` queda libre para pruebas.

## URL base para apps

```text
https://api.tudominio.com
```

Ejemplos:

```text
https://api.tudominio.com/api/auth/login
https://api.tudominio.com/api/articulos
https://api.tudominio.com/api/ventas
```

## Importante

La base queda persistente en el volumen `carnes_luevanos_data`. Si reconstruyes el contenedor, no se borra.
Para respaldar:

```bash
./backup_database.sh
```

Para actualizar:

```bash
./update_server.sh
```

Para restaurar un respaldo:

```bash
./restore_database.sh backups/database_YYYYMMDD_HHMMSS.db
```
