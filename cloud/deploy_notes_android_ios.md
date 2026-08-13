# Conexion Android/iOS

Cuando el servidor este desplegado, usa esta URL base en las apps:

```text
https://api.tudominio.com
```

Todas las peticiones protegidas deben mandar:

```http
X-API-Key: TU_CLAVE_DE_CLOUD_ENV
```

Endpoints principales:

```text
GET  /api/health
POST /api/auth/login
GET  /api/articulos
POST /api/articulos
GET  /api/clientes
GET  /api/proveedores
GET  /api/ventas
POST /api/ventas
```

Prueba rapida:

```bash
curl https://api.tudominio.com/api/health
curl -H "X-API-Key: TU_CLAVE" https://api.tudominio.com/api/articulos
```
