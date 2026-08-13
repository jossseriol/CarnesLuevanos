import sqlite3

SUPERUSER_USERNAME = "Ernesto Luevanos"

MODULOS_SISTEMA = [
    ("ventas", "Ventas"),
    ("inventario", "Inventario"),
    ("clientes", "Clientes"),
    ("pedidos", "Pedidos"),
    ("proveedores", "Proveedores"),
    ("compras", "Compras"),
    ("rendimiento", "Rendimiento"),
    ("informacion", "Informacion"),
    ("configuracion", "Configuracion"),
]


def conectar():
    return sqlite3.connect("database.db")


def asegurar_tablas_permisos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(usuarios)")
    columnas = {fila[1] for fila in cursor.fetchall()}
    if "nombre" not in columnas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN nombre TEXT")
    if "rol" not in columnas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN rol TEXT DEFAULT 'usuario'")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS permisos_usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            modulo TEXT NOT NULL,
            permitido INTEGER NOT NULL DEFAULT 0,
            UNIQUE(usuario_id, modulo),
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    conn.close()


def es_superusuario(username):
    return (username or "").strip().lower() == SUPERUSER_USERNAME.lower()


def obtener_usuario(username):
    asegurar_tablas_permisos()
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, COALESCE(nombre, username), COALESCE(rol, 'usuario') FROM usuarios WHERE username = ?", (username,))
    usuario = cursor.fetchone()
    conn.close()
    return usuario


def tiene_permiso(username, modulo):
    if es_superusuario(username):
        return True

    usuario = obtener_usuario(username)
    if not usuario:
        return False

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT permitido FROM permisos_usuario WHERE usuario_id = ? AND modulo = ?",
        (usuario[0], modulo),
    )
    fila = cursor.fetchone()
    conn.close()
    return bool(fila and fila[0])


def tiene_permiso_accion(username, permiso):
    """Validación granular para cada operación (por ejemplo, ventas.cancelar)."""
    from modulos.auth.seguridad import has_permission
    return has_permission(username, permiso)


def obtener_permisos_usuario(usuario_id):
    asegurar_tablas_permisos()
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT modulo, permitido FROM permisos_usuario WHERE usuario_id = ?", (usuario_id,))
    permisos = {modulo: bool(permitido) for modulo, permitido in cursor.fetchall()}
    conn.close()
    return permisos


def guardar_permisos_usuario(usuario_id, permisos):
    asegurar_tablas_permisos()
    conn = conectar()
    cursor = conn.cursor()
    for modulo, permitido in permisos.items():
        cursor.execute(
            """
            INSERT INTO permisos_usuario (usuario_id, modulo, permitido)
            VALUES (?, ?, ?)
            ON CONFLICT(usuario_id, modulo) DO UPDATE SET permitido = excluded.permitido
            """,
            (usuario_id, modulo, 1 if permitido else 0),
        )
    conn.commit()
    conn.close()


def permisos_por_defecto():
    return {clave: (clave == "informacion") for clave, _ in MODULOS_SISTEMA}

