PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS abonos_compras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    compra_id INTEGER NOT NULL,
    monto REAL NOT NULL,
    fecha TEXT NOT NULL,
    hora TEXT NOT NULL,
    nota TEXT
);

CREATE TABLE IF NOT EXISTS abonos_mobile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    persona TEXT NOT NULL,
    concepto TEXT NOT NULL,
    monto REAL NOT NULL DEFAULT 0,
    referencia TEXT,
    fecha TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'Registrado'
);

CREATE TABLE IF NOT EXISTS abonos_prestamos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prestamo_id INTEGER NOT NULL,
    monto REAL NOT NULL,
    fecha TEXT NOT NULL,
    nota TEXT
);

CREATE TABLE IF NOT EXISTS abonos_ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL,
    monto REAL NOT NULL,
    fecha TEXT NOT NULL,
    hora TEXT NOT NULL,
    nota TEXT
);

CREATE TABLE IF NOT EXISTS articulos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE,
    articulo TEXT NOT NULL,
    precio REAL NOT NULL,
    costo REAL NOT NULL,
    stock INTEGER NOT NULL,
    estado TEXT NOT NULL,
    imagen_path TEXT
);

CREATE TABLE IF NOT EXISTS auditoria_ia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    accion TEXT,
    argumentos TEXT,
    exito INTEGER,
    fecha TEXT
);

CREATE TABLE IF NOT EXISTS auditoria_seguridad (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    usuario_id INTEGER,
    evento TEXT NOT NULL,
    detalle TEXT,
    dispositivo_id TEXT,
    exito INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    cedula NUMERIC,
    celular NUMERIC,
    direccion TEXT,
    correo TEXT
);

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
    notas TEXT,
    tipo_pago TEXT DEFAULT 'Contado',
    monto_pagado REAL DEFAULT 0,
    saldo REAL DEFAULT 0,
    estado_pago TEXT DEFAULT 'Pagado'
);

CREATE TABLE IF NOT EXISTS configuracion_sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clave TEXT UNIQUE NOT NULL,
    valor TEXT NOT NULL,
    descripcion TEXT,
    fecha_modificacion TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS confirmaciones_criticas (
    token TEXT PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    operacion TEXT NOT NULL,
    creado TEXT NOT NULL,
    expira TEXT NOT NULL,
    usado INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS detalle_ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER,
    producto TEXT,
    precio_unitario REAL,
    cantidad INTEGER,
    subtotal REAL,
    FOREIGN KEY (venta_id) REFERENCES ventas (id)
);

CREATE TABLE IF NOT EXISTS dispositivos_autorizados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    dispositivo_id TEXT NOT NULL,
    nombre TEXT,
    autorizado INTEGER NOT NULL DEFAULT 1,
    creado TEXT NOT NULL,
    ultimo_uso TEXT,
    UNIQUE(usuario_id, dispositivo_id),
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dispositivos_mfa_confiables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL,
    confiable_hasta TEXT NOT NULL,
    creado TEXT NOT NULL,
    ultimo_uso TEXT NOT NULL,
    UNIQUE(usuario_id, token_hash),
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS empacadora_clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    telefono TEXT,
    direccion TEXT,
    notas TEXT,
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS empacadora_cobranza (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lote INTEGER NOT NULL,
    periodo_inicio TEXT NOT NULL,
    periodo_fin TEXT NOT NULL,
    fecha_compra TEXT NOT NULL,
    cliente TEXT NOT NULL,
    folio TEXT NOT NULL,
    monto REAL DEFAULT 0,
    abono REAL DEFAULT 0,
    saldo REAL DEFAULT 0,
    status TEXT DEFAULT 'Pendiente',
    fecha_pago TEXT,
    usuario_recibe TEXT,
    nota TEXT,
    recordatorio TEXT,
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS empacadora_lotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lote INTEGER NOT NULL,
    periodo_inicio TEXT NOT NULL,
    periodo_fin TEXT NOT NULL,
    canal TEXT,
    fecha_introduccion TEXT NOT NULL,
    proveedor TEXT,
    producto TEXT NOT NULL,
    peso REAL DEFAULT 0,
    precio REAL DEFAULT 0,
    monto REAL DEFAULT 0,
    observaciones TEXT,
    destino TEXT,
    origen TEXT,
    folio_venta TEXT,
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS empacadora_ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    cliente TEXT NOT NULL,
    folio TEXT NOT NULL,
    monto REAL NOT NULL DEFAULT 0,
    lote INTEGER NOT NULL,
    creado_en TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS eventos_sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    titulo TEXT NOT NULL,
    mensaje TEXT NOT NULL,
    usuario TEXT,
    origen TEXT,
    fecha TEXT NOT NULL,
    leido INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS historial_actividades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,
    hora TEXT NOT NULL,
    usuario TEXT DEFAULT 'Sistema',
    modulo TEXT NOT NULL,
    accion TEXT NOT NULL,
    descripcion TEXT,
    detalles TEXT,
    tipo TEXT DEFAULT 'INFO'
);

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
);

CREATE TABLE IF NOT EXISTS notificaciones_sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    titulo TEXT NOT NULL,
    mensaje TEXT NOT NULL,
    fecha TEXT NOT NULL,
    hora TEXT NOT NULL,
    leida INTEGER DEFAULT 0,
    clave TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    cliente_nombre TEXT NOT NULL,
    fecha TEXT NOT NULL,
    estado TEXT DEFAULT 'Pendiente',
    total REAL DEFAULT 0.0,
    observaciones TEXT,
    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
);

CREATE TABLE IF NOT EXISTS pedidos_detalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER,
    producto_codigo TEXT NOT NULL,
    producto_nombre TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL DEFAULT 0.0,
    subtotal REAL DEFAULT 0.0,
    FOREIGN KEY (pedido_id) REFERENCES pedidos_proveedor (id)
);

CREATE TABLE IF NOT EXISTS pedidos_proveedor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proveedor_nombre TEXT NOT NULL,
    fecha TEXT NOT NULL,
    estado TEXT DEFAULT 'Pendiente',
    total REAL DEFAULT 0.0,
    observaciones TEXT
);

CREATE TABLE IF NOT EXISTS permisos_accion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    permiso TEXT NOT NULL,
    permitido INTEGER NOT NULL DEFAULT 0,
    UNIQUE(usuario_id, permiso),
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS permisos_usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    modulo TEXT NOT NULL,
    permitido INTEGER NOT NULL DEFAULT 0,
    UNIQUE(usuario_id, modulo),
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

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
);

CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL,
    costo REAL NOT NULL,
    stock INTEGER NOT NULL,
    estado TEXT DEFAULT 'Activo',
    imagen_path TEXT
);

CREATE TABLE IF NOT EXISTS proveedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa TEXT NOT NULL,
    rif TEXT UNIQUE NOT NULL,
    celular TEXT,
    direccion TEXT,
    correo TEXT
);

CREATE TABLE IF NOT EXISTS sesiones_usuario (
    id TEXT PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    dispositivo_id TEXT NOT NULL,
    inicio TEXT NOT NULL,
    ultima_actividad TEXT NOT NULL,
    expira TEXT NOT NULL,
    cerrada TEXT,
    motivo_cierre TEXT,
    ip TEXT,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    nombre TEXT,
    rol TEXT DEFAULT 'usuario',
    numero_empleado TEXT,
    sucursal TEXT,
    horario_inicio TEXT,
    horario_fin TEXT,
    estado TEXT NOT NULL DEFAULT 'activo',
    ultimo_acceso TEXT,
    password_cambiada TEXT,
    password_vence TEXT,
    intentos_fallidos INTEGER NOT NULL DEFAULT 0,
    bloqueado_hasta TEXT,
    mfa_secret TEXT,
    mfa_habilitado INTEGER NOT NULL DEFAULT 0,
    telefono TEXT,
    requiere_cambio_password INTEGER NOT NULL DEFAULT 0,
    foto_perfil TEXT
);

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
    costo REAL,
    numero_factura INTEGER,
    subtotal REAL DEFAULT 0,
    iva REAL DEFAULT 0,
    monto_recibido REAL DEFAULT 0,
    cambio REAL DEFAULT 0,
    folio TEXT,
    tipo_pago TEXT DEFAULT 'Contado',
    saldo REAL DEFAULT 0,
    estado_pago TEXT DEFAULT 'Pagado',
    direccion_cliente TEXT,
    telefono_cliente TEXT,
    vendedor TEXT,
    nota_imagen TEXT
);

CREATE INDEX IF NOT EXISTS idx_sesiones_usuario_abiertas
ON sesiones_usuario(usuario_id, cerrada);
