SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS clientes (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255),
    cedula VARCHAR(100),
    celular VARCHAR(100),
    direccion TEXT,
    correo VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS articulos (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(100) UNIQUE,
    articulo VARCHAR(255) NOT NULL,
    precio DECIMAL(12,2) NOT NULL,
    costo DECIMAL(12,2) NOT NULL,
    stock INT NOT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'activo',
    imagen_path TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS proveedores (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    empresa VARCHAR(255) NOT NULL,
    rif VARCHAR(100) NOT NULL UNIQUE,
    celular VARCHAR(100),
    direccion TEXT,
    correo VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS productos (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(100) UNIQUE,
    nombre VARCHAR(255) NOT NULL,
    precio DECIMAL(12,2) NOT NULL,
    costo DECIMAL(12,2) NOT NULL,
    stock INT NOT NULL,
    estado VARCHAR(50) DEFAULT 'Activo',
    imagen_path TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password TEXT NOT NULL,
    nombre VARCHAR(255),
    rol VARCHAR(100) DEFAULT 'usuario',
    numero_empleado VARCHAR(100),
    sucursal VARCHAR(255),
    horario_inicio VARCHAR(100),
    horario_fin VARCHAR(100),
    estado VARCHAR(50) NOT NULL DEFAULT 'activo',
    ultimo_acceso TEXT,
    password_cambiada TEXT,
    password_vence TEXT,
    intentos_fallidos INT NOT NULL DEFAULT 0,
    bloqueado_hasta TEXT,
    mfa_secret TEXT,
    mfa_habilitado INT NOT NULL DEFAULT 0,
    telefono VARCHAR(100),
    requiere_cambio_password INT NOT NULL DEFAULT 0,
    foto_perfil TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ventas (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    factura INT,
    cliente VARCHAR(255),
    articulo VARCHAR(255),
    precio DECIMAL(12,2),
    cantidad INT,
    total DECIMAL(12,2),
    fecha VARCHAR(50),
    hora VARCHAR(50),
    costo DECIMAL(12,2),
    numero_factura INT,
    subtotal DECIMAL(12,2) DEFAULT 0,
    iva DECIMAL(12,2) DEFAULT 0,
    monto_recibido DECIMAL(12,2) DEFAULT 0,
    cambio DECIMAL(12,2) DEFAULT 0,
    folio VARCHAR(255),
    tipo_pago VARCHAR(100) DEFAULT 'Contado',
    saldo DECIMAL(12,2) DEFAULT 0,
    estado_pago VARCHAR(100) DEFAULT 'Pagado',
    direccion_cliente TEXT,
    telefono_cliente VARCHAR(100),
    vendedor VARCHAR(255),
    nota_imagen TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS detalle_ventas (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    venta_id INT,
    producto VARCHAR(255),
    precio_unitario DECIMAL(12,2),
    cantidad INT,
    subtotal DECIMAL(12,2),
    FOREIGN KEY (venta_id) REFERENCES ventas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS compras (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    proveedor VARCHAR(255) NOT NULL,
    factura VARCHAR(255),
    producto VARCHAR(255) NOT NULL,
    cantidad INT NOT NULL,
    costo_unitario DECIMAL(12,2) NOT NULL,
    total DECIMAL(12,2) NOT NULL,
    fecha VARCHAR(50) NOT NULL,
    estado VARCHAR(100) NOT NULL,
    notas TEXT,
    tipo_pago VARCHAR(100) DEFAULT 'Contado',
    monto_pagado DECIMAL(12,2) DEFAULT 0,
    saldo DECIMAL(12,2) DEFAULT 0,
    estado_pago VARCHAR(100) DEFAULT 'Pagado'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS abonos_compras (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    compra_id INT NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    fecha VARCHAR(50) NOT NULL,
    hora VARCHAR(50) NOT NULL,
    nota TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS abonos_mobile (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    persona VARCHAR(255) NOT NULL,
    concepto VARCHAR(255) NOT NULL,
    monto DECIMAL(12,2) NOT NULL DEFAULT 0,
    referencia VARCHAR(255),
    fecha VARCHAR(50) NOT NULL,
    estado VARCHAR(100) NOT NULL DEFAULT 'Registrado'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS prestamos (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    beneficiario VARCHAR(255) NOT NULL,
    concepto TEXT,
    monto DECIMAL(12,2) NOT NULL,
    pagado DECIMAL(12,2) DEFAULT 0,
    saldo DECIMAL(12,2) NOT NULL,
    fecha VARCHAR(50) NOT NULL,
    vencimiento VARCHAR(50),
    estado VARCHAR(100) NOT NULL,
    notas TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS abonos_prestamos (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    prestamo_id INT NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    fecha VARCHAR(50) NOT NULL,
    nota TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS abonos_ventas (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    venta_id INT NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    fecha VARCHAR(50) NOT NULL,
    hora VARCHAR(50) NOT NULL,
    nota TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS pedidos (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT,
    cliente_nombre VARCHAR(255) NOT NULL,
    fecha VARCHAR(50) NOT NULL,
    estado VARCHAR(100) DEFAULT 'Pendiente',
    total DECIMAL(12,2) DEFAULT 0,
    observaciones TEXT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS pedidos_proveedor (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    proveedor_nombre VARCHAR(255) NOT NULL,
    fecha VARCHAR(50) NOT NULL,
    estado VARCHAR(100) DEFAULT 'Pendiente',
    total DECIMAL(12,2) DEFAULT 0,
    observaciones TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS pedidos_detalle (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    pedido_id INT,
    producto_codigo VARCHAR(100) NOT NULL,
    producto_nombre VARCHAR(255) NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(12,2) DEFAULT 0,
    subtotal DECIMAL(12,2) DEFAULT 0,
    FOREIGN KEY (pedido_id) REFERENCES pedidos_proveedor(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS permisos_usuario (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    modulo VARCHAR(255) NOT NULL,
    permitido INT NOT NULL DEFAULT 0,
    UNIQUE KEY uq_permiso_usuario (usuario_id, modulo),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS permisos_accion (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    permiso VARCHAR(255) NOT NULL,
    permitido INT NOT NULL DEFAULT 0,
    UNIQUE KEY uq_permiso_accion (usuario_id, permiso),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS sesiones_usuario (
    id VARCHAR(255) PRIMARY KEY,
    usuario_id INT NOT NULL,
    dispositivo_id VARCHAR(255) NOT NULL,
    inicio TEXT NOT NULL,
    ultima_actividad TEXT NOT NULL,
    expira TEXT NOT NULL,
    cerrada TEXT,
    motivo_cierre TEXT,
    ip VARCHAR(100),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;



CREATE TABLE IF NOT EXISTS dispositivos_autorizados (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    dispositivo_id VARCHAR(255) NOT NULL,
    nombre VARCHAR(255),
    autorizado INT NOT NULL DEFAULT 1,
    creado TEXT NOT NULL,
    ultimo_uso TEXT,
    UNIQUE KEY uq_dispositivo_autorizado (usuario_id, dispositivo_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS dispositivos_mfa_confiables (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    confiable_hasta TEXT NOT NULL,
    creado TEXT NOT NULL,
    ultimo_uso TEXT NOT NULL,
    UNIQUE KEY uq_mfa_confiable (usuario_id, token_hash),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS auditoria_ia (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(255),
    accion TEXT,
    argumentos TEXT,
    exito INT,
    fecha VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS auditoria_seguridad (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    fecha VARCHAR(50) NOT NULL,
    usuario_id INT,
    evento VARCHAR(255) NOT NULL,
    detalle TEXT,
    dispositivo_id VARCHAR(255),
    exito INT NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS configuracion_sistema (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    clave VARCHAR(255) NOT NULL UNIQUE,
    valor TEXT NOT NULL,
    descripcion TEXT,
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS confirmaciones_criticas (
    token VARCHAR(255) PRIMARY KEY,
    usuario_id INT NOT NULL,
    operacion VARCHAR(255) NOT NULL,
    creado TEXT NOT NULL,
    expira TEXT NOT NULL,
    usado INT NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS empacadora_clientes (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    telefono VARCHAR(100),
    direccion TEXT,
    notas TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS empacadora_cobranza (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    lote INT NOT NULL,
    periodo_inicio VARCHAR(50) NOT NULL,
    periodo_fin VARCHAR(50) NOT NULL,
    fecha_compra VARCHAR(50) NOT NULL,
    cliente VARCHAR(255) NOT NULL,
    folio VARCHAR(255) NOT NULL,
    monto DECIMAL(12,2) DEFAULT 0,
    abono DECIMAL(12,2) DEFAULT 0,
    saldo DECIMAL(12,2) DEFAULT 0,
    status VARCHAR(100) DEFAULT 'Pendiente',
    fecha_pago VARCHAR(50),
    usuario_recibe VARCHAR(255),
    nota TEXT,
    recordatorio TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS empacadora_lotes (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    lote INT NOT NULL,
    periodo_inicio VARCHAR(50) NOT NULL,
    periodo_fin VARCHAR(50) NOT NULL,
    canal VARCHAR(255),
    fecha_introduccion VARCHAR(50) NOT NULL,
    proveedor VARCHAR(255),
    producto VARCHAR(255) NOT NULL,
    peso DECIMAL(12,2) DEFAULT 0,
    precio DECIMAL(12,2) DEFAULT 0,
    monto DECIMAL(12,2) DEFAULT 0,
    observaciones TEXT,
    destino VARCHAR(255),
    origen VARCHAR(255),
    folio_venta VARCHAR(255),
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS empacadora_ventas (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    fecha VARCHAR(50) NOT NULL,
    cliente VARCHAR(255) NOT NULL,
    folio VARCHAR(255) NOT NULL,
    monto DECIMAL(12,2) NOT NULL DEFAULT 0,
    lote INT NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS eventos_sistema (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(100) NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    mensaje TEXT NOT NULL,
    usuario VARCHAR(255),
    origen VARCHAR(255),
    fecha VARCHAR(50) NOT NULL,
    leido INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS historial_actividades (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    fecha VARCHAR(50) NOT NULL,
    hora VARCHAR(50) NOT NULL,
    usuario VARCHAR(255) DEFAULT 'Sistema',
    modulo VARCHAR(255) NOT NULL,
    accion VARCHAR(255) NOT NULL,
    descripcion TEXT,
    detalles TEXT,
    tipo VARCHAR(100) DEFAULT 'INFO'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS nominas (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    empleado VARCHAR(255) NOT NULL,
    puesto VARCHAR(255),
    periodo VARCHAR(100) NOT NULL,
    sueldo DECIMAL(12,2) NOT NULL,
    bonos DECIMAL(12,2) DEFAULT 0,
    deducciones DECIMAL(12,2) DEFAULT 0,
    neto DECIMAL(12,2) NOT NULL,
    fecha VARCHAR(50) NOT NULL,
    estado VARCHAR(100) NOT NULL,
    notas TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS notificaciones_sistema (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(100) NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    mensaje TEXT NOT NULL,
    fecha VARCHAR(50) NOT NULL,
    hora VARCHAR(50) NOT NULL,
    leida INT DEFAULT 0,
    clave VARCHAR(255) UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;