# modelos/database.py
import sqlite3
import sys
def crear_base_de_datos():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Tabla de artículos (con código de barras)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articulos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                articulo TEXT NOT NULL,
                precio REAL NOT NULL,
                costo REAL NOT NULL,
                stock INTEGER NOT NULL,
                estado TEXT NOT NULL,
                imagen_path TEXT
            )
        ''')
        
        # Agregar columna codigo si no existe (para bases de datos existentes)
        try:
            cursor.execute("ALTER TABLE articulos ADD COLUMN codigo TEXT UNIQUE")
            print("Columna 'codigo' agregada a tabla articulos")
        except sqlite3.OperationalError:
            # La columna ya existe, continuar
            pass

        # Tabla de clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                cedula NUMERIC,
                celular NUMERIC,
                direccion TEXT,
                correo TEXT
            )
        ''')

        # Tabla de usuarios y permisos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                nombre TEXT,
                rol TEXT DEFAULT 'usuario'
            )
        ''')

        cursor.execute("PRAGMA table_info(usuarios)")
        columnas_usuarios = {fila[1] for fila in cursor.fetchall()}
        if "nombre" not in columnas_usuarios:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN nombre TEXT")
        if "rol" not in columnas_usuarios:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN rol TEXT DEFAULT 'usuario'")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permisos_usuario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                modulo TEXT NOT NULL,
                permitido INTEGER NOT NULL DEFAULT 0,
                UNIQUE(usuario_id, modulo),
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
            )
        ''')

        # Tabla de ventas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factura INTEGER,
                cliente TEXT,
                articulo TEXT,
                precio REAL,
                cantidad INTEGER,
                total REAL,
                fecha TEXT,
                hora TEXT,
                costo REAL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa TEXT NOT NULL,
                rif TEXT UNIQUE NOT NULL,  -- UNIQUE para evitar RIFs repetidos
                celular TEXT,
                direccion TEXT,
                correo TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor TEXT NOT NULL,
                factura TEXT,
                producto TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                costo_unitario REAL NOT NULL,
                total REAL NOT NULL,
                fecha TEXT NOT NULL,
                estado TEXT NOT NULL,
                notas TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prestamos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                beneficiario TEXT NOT NULL,
                concepto TEXT,
                monto REAL NOT NULL,
                pagado REAL DEFAULT 0,
                saldo REAL NOT NULL,
                fecha TEXT NOT NULL,
                vencimiento TEXT,
                estado TEXT NOT NULL,
                notas TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS abonos_prestamos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prestamo_id INTEGER NOT NULL,
                monto REAL NOT NULL,
                fecha TEXT NOT NULL,
                nota TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nominas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empleado TEXT NOT NULL,
                puesto TEXT,
                periodo TEXT NOT NULL,
                sueldo REAL NOT NULL,
                bonos REAL DEFAULT 0,
                deducciones REAL DEFAULT 0,
                neto REAL NOT NULL,
                fecha TEXT NOT NULL,
                estado TEXT NOT NULL,
                notas TEXT
            )
        ''')


        cursor.execute('''
            CREATE TABLE IF NOT EXISTS eventos_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                titulo TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                usuario TEXT,
                origen TEXT,
                fecha TEXT NOT NULL,
                leido INTEGER DEFAULT 0
            )
        ''')

        # Superusuario principal. Nunca se vuelve a escribir la contraseña al arrancar.
        cursor.execute("SELECT id FROM usuarios WHERE username IN (?, ?) ORDER BY id LIMIT 1", ("admin", "Ernesto Luevanos"))
        super_usuario = cursor.fetchone()
        if super_usuario:
            super_id = super_usuario[0]
            cursor.execute(
                "UPDATE usuarios SET nombre = COALESCE(nombre, ?), rol = 'super' WHERE id = ?",
                ("Administrador Luévanos", super_id)
            )
        else:
            import os, secrets
            from modulos.auth.seguridad import hash_password
            initial_password = os.getenv("CARNES_LUEVANOS_INITIAL_ADMIN_PASSWORD") or secrets.token_urlsafe(15)
            cursor.execute(
                "INSERT INTO usuarios (username, password, nombre, rol) VALUES (?, ?, ?, 'super')",
                ("admin", hash_password(initial_password), "Administrador Luévanos")
            )
            super_id = cursor.lastrowid
            print(f"CLAVE ADMINISTRATIVA INICIAL (guardar y cambiar): {initial_password}")

        for modulo in ("ventas", "inventario", "clientes", "pedidos", "proveedores", "compras", "rendimiento", "informacion", "configuracion"):
            cursor.execute(
                "SELECT id FROM permisos_usuario WHERE usuario_id = ? AND modulo = ?",
                (super_id, modulo)
            )
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE permisos_usuario SET permitido = 1 WHERE usuario_id = ? AND modulo = ?",
                    (super_id, modulo)
                )
            else:
                cursor.execute(
                    "INSERT INTO permisos_usuario (usuario_id, modulo, permitido) VALUES (?, ?, 1)",
                    (super_id, modulo)
                )
        conn.commit()
        conn.close()
        from modulos.auth.seguridad import ensure_security_schema
        ensure_security_schema()
        print("Base de datos y tablas creadas (o ya existentes).")

    except sqlite3.Error as e:
        print(f"Error al crear la base de datos: {e}")
        sys.exit()  # Salir de la app si no se puede crear la base de datos
