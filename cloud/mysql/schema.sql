CREATE DATABASE IF NOT EXISTS carnes_luevanos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE carnes_luevanos;

CREATE TABLE IF NOT EXISTS articulos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  codigo VARCHAR(100),
  articulo VARCHAR(255) NOT NULL,
  precio DECIMAL(12,2) NOT NULL,
  costo DECIMAL(12,2) NOT NULL,
  stock INT NOT NULL,
  estado VARCHAR(50) NOT NULL DEFAULT 'Activo',
  imagen_path TEXT,
  INDEX idx_articulos_codigo (codigo),
  INDEX idx_articulos_articulo (articulo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS productos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  codigo VARCHAR(100),
  nombre VARCHAR(255) NOT NULL,
  precio DECIMAL(12,2) NOT NULL,
  costo DECIMAL(12,2) NOT NULL,
  stock INT NOT NULL,
  estado VARCHAR(50) DEFAULT 'Activo',
  imagen_path TEXT,
  INDEX idx_productos_codigo (codigo),
  INDEX idx_productos_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS clientes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(255),
  cedula VARCHAR(50),
  celular VARCHAR(50),
  direccion TEXT,
  correo VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS proveedores (
  id INT AUTO_INCREMENT PRIMARY KEY,
  empresa VARCHAR(255) NOT NULL,
  rif VARCHAR(100) NOT NULL,
  celular VARCHAR(50),
  direccion TEXT,
  correo VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS compras (
  id INT AUTO_INCREMENT PRIMARY KEY,
  proveedor VARCHAR(255) NOT NULL,
  factura VARCHAR(100),
  producto VARCHAR(255) NOT NULL,
  cantidad INT NOT NULL,
  costo_unitario DECIMAL(12,2) NOT NULL,
  total DECIMAL(12,2) NOT NULL,
  fecha VARCHAR(20) NOT NULL,
  estado VARCHAR(50) NOT NULL,
  notas TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ventas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  factura INT,
  cliente VARCHAR(255),
  articulo VARCHAR(255),
  precio DECIMAL(12,2),
  cantidad INT,
  total DECIMAL(12,2),
  fecha VARCHAR(20),
  hora VARCHAR(20),
  costo DECIMAL(12,2),
  INDEX idx_ventas_factura (factura),
  INDEX idx_ventas_fecha (fecha)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS detalle_ventas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  venta_id INT,
  producto VARCHAR(255),
  precio_unitario DECIMAL(12,2),
  cantidad INT,
  subtotal DECIMAL(12,2),
  INDEX idx_detalle_venta_id (venta_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pedidos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT,
  cliente_nombre VARCHAR(255) NOT NULL,
  fecha VARCHAR(20) NOT NULL,
  estado VARCHAR(50) DEFAULT 'Pendiente',
  total DECIMAL(12,2) DEFAULT 0.00,
  observaciones TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pedidos_detalle (
  id INT AUTO_INCREMENT PRIMARY KEY,
  pedido_id INT,
  producto_codigo VARCHAR(100) NOT NULL,
  producto_nombre VARCHAR(255) NOT NULL,
  cantidad INT NOT NULL,
  precio_unitario DECIMAL(12,2) DEFAULT 0.00,
  subtotal DECIMAL(12,2) DEFAULT 0.00,
  INDEX idx_pedidos_detalle_pedido (pedido_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pedidos_proveedor (
  id INT AUTO_INCREMENT PRIMARY KEY,
  proveedor_nombre VARCHAR(255) NOT NULL,
  fecha VARCHAR(20) NOT NULL,
  estado VARCHAR(50) DEFAULT 'Pendiente',
  total DECIMAL(12,2) DEFAULT 0.00,
  observaciones TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  nombre VARCHAR(255),
  rol VARCHAR(50) DEFAULT 'usuario'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS permisos_usuario (
  id INT AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT NOT NULL,
  modulo VARCHAR(100) NOT NULL,
  permitido TINYINT NOT NULL DEFAULT 0,
  UNIQUE KEY uq_permiso_usuario_modulo (usuario_id, modulo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS configuracion_sistema (
  id INT AUTO_INCREMENT PRIMARY KEY,
  clave VARCHAR(100) NOT NULL UNIQUE,
  valor TEXT NOT NULL,
  descripcion TEXT,
  fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS eventos_sistema (
  id INT AUTO_INCREMENT PRIMARY KEY,
  tipo VARCHAR(100) NOT NULL,
  titulo VARCHAR(255) NOT NULL,
  mensaje TEXT NOT NULL,
  usuario VARCHAR(255),
  origen VARCHAR(100),
  fecha VARCHAR(30) NOT NULL,
  leido TINYINT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS historial_actividades (
  id INT AUTO_INCREMENT PRIMARY KEY,
  fecha VARCHAR(20) NOT NULL,
  hora VARCHAR(20) NOT NULL,
  usuario VARCHAR(255) DEFAULT 'Sistema',
  modulo VARCHAR(100) NOT NULL,
  accion VARCHAR(100) NOT NULL,
  descripcion TEXT,
  detalles TEXT,
  tipo VARCHAR(50) DEFAULT 'INFO'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO usuarios (username, password, nombre, rol)
VALUES ('Ernesto Luevanos', '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5', 'Ernesto Luevanos', 'superusuario')
ON DUPLICATE KEY UPDATE
  password = VALUES(password),
  nombre = VALUES(nombre),
  rol = VALUES(rol);

INSERT INTO configuracion_sistema (clave, valor, descripcion)
VALUES ('iva_porcentaje', '16', 'Porcentaje de IVA para ventas')
ON DUPLICATE KEY UPDATE valor = VALUES(valor);
