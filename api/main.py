from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import API_PREFIX, API_SECRET_KEY, CORS_ORIGINS, DATABASE_PATH
from .database import ensure_database_ready, get_connection
from .routers import articulos, auth, clientes, compras, eventos_sistema, mobile, pedidos, proveedores, ventas


app = FastAPI(
    title="Carnes Luévanos API",
    description="API cloud para comunicar Carnes Luévanos con Android/iOS.",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    ensure_database_ready()


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if API_SECRET_KEY and request.url.path.startswith(API_PREFIX) and request.url.path != f"{API_PREFIX}/health":
        token = request.headers.get("x-api-key", "")
        if token != API_SECRET_KEY:
            return JSONResponse(status_code=401, content={"detail": "API key invalida"})
    return await call_next(request)


@app.get("/")
def root():
    return {
        "app": "Carnes Luévanos API",
        "docs": "/docs",
        "health": f"{API_PREFIX}/health",
    }


@app.get(f"{API_PREFIX}/health")
def health():
    counts = {}
    auth_database_path = None
    auth_database_matches = False
    try:
        conn = get_connection()
        try:
            for table in ("articulos", "clientes", "proveedores", "ventas", "compras", "pedidos_proveedor"):
                try:
                    row = conn.execute(f"SELECT COUNT(*) AS total FROM {table}").fetchone()
                    counts[table] = int(row["total"] if hasattr(row, "keys") else row[0])
                except Exception:
                    counts[table] = None
        finally:
            conn.close()
    except Exception:
        counts = {}
    try:
        from modulos.auth.seguridad import DB_PATH as security_database_path

        auth_database_path = str(security_database_path)
        auth_database_matches = security_database_path.resolve() == DATABASE_PATH.resolve()
    except Exception:
        auth_database_path = None
    return {
        "status": "ok" if auth_database_matches else "degraded",
        "database_path": str(DATABASE_PATH),
        "auth_database_path": auth_database_path,
        "auth_database_matches": auth_database_matches,
        "counts": counts,
    }


app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(articulos.router, prefix=API_PREFIX)
app.include_router(clientes.router, prefix=API_PREFIX)
app.include_router(proveedores.router, prefix=API_PREFIX)
app.include_router(pedidos.router, prefix=API_PREFIX)
app.include_router(compras.router, prefix=API_PREFIX)
app.include_router(eventos_sistema.router, prefix=API_PREFIX)
app.include_router(ventas.router, prefix=API_PREFIX)
app.include_router(mobile.router, prefix=API_PREFIX)

