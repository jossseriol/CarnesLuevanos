# Servidor Cloud con MySQL usando IP publica

Esta opcion no necesita dominio. El API queda disponible en:

```text
http://TU_IP_PUBLICA/api
```

## Pasos en el VPS

1. Compra un VPS Ubuntu 22.04/24.04.
2. Abre el puerto `80` en el firewall del proveedor.
3. Instala Docker:

```bash
sudo apt update
sudo apt install -y ca-certificates curl git unzip
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

4. Sube el proyecto al servidor y entra a la carpeta `cloud`.
5. Crea el archivo `.env`:

```bash
cp .env.mysql-ip.example .env
nano .env
```

6. Cambia `TU_IP_PUBLICA` por la IP real del servidor y cambia todas las claves.
7. Levanta el servidor:

```bash
docker compose -f docker-compose.mysql-ip.yml --env-file .env up -d --build
```

8. Prueba:

```bash
curl http://TU_IP_PUBLICA/api/health
```

## URL para Android/iOS

Usa:

```text
http://TU_IP_PUBLICA/api
```

En las peticiones privadas manda:

```text
X-API-Key: tu_API_SECRET_KEY
```

## Nota importante

Esta opcion usa HTTP porque no hay dominio. Funciona para arrancar, pero para entrega final al cliente conviene migrar a dominio con HTTPS.
