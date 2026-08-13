# Servidor Cloud con MySQL

Esta es la opcion recomendada para operar el API desde Android, iOS y el sistema de escritorio con una base de datos central en la nube.

Si todavia no tienes dominio, usa primero `README_DEPLOY_MYSQL_IP.md`. Esa variante publica el API en:

```text
http://TU_IP_PUBLICA/api
```

## Archivos importantes

- `docker-compose.mysql.yml`: levanta MySQL, API y Caddy con SSL.
- `docker-compose.mysql-ip.yml`: levanta MySQL, API y Caddy por IP publica sin dominio.
- `.env.mysql.example`: variables privadas del servidor.
- `.env.mysql-ip.example`: variables para usar IP publica.
- `mysql/schema.sql`: tablas iniciales y super usuario.
- `Dockerfile.mysql`: imagen del API con soporte MySQL.

## Instalacion rapida en VPS Ubuntu

1. Compra un VPS Ubuntu 22.04/24.04.
2. Apunta tu dominio o subdominio al IP del VPS, por ejemplo `api.tudominio.com`.
3. Instala Docker:

```bash
sudo apt update
sudo apt install -y ca-certificates curl git unzip
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

4. Sube este proyecto al servidor y entra a la carpeta `cloud`.
5. Crea tu archivo `.env`:

```bash
cp .env.mysql.example .env
nano .env
```

6. Levanta el servidor:

```bash
docker compose -f docker-compose.mysql.yml --env-file .env up -d --build
```

7. Prueba el API:

```bash
curl https://api.tudominio.com/api/health
```

## Conexion desde Android/iOS

Usa la URL publica:

```text
https://api.tudominio.com/api
```

En cada request protegida manda el header:

```text
X-API-Key: tu_clave_API_SECRET_KEY
```

## Respaldo MySQL

```bash
chmod +x backup_mysql.sh
./backup_mysql.sh
```

## Restaurar respaldo

```bash
chmod +x restore_mysql.sh
./restore_mysql.sh backups/carnes_luevanos_mysql_YYYYMMDD_HHMMSS.sql
```
