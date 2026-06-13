-- Script de inicialización de base de datos
-- Database: DBLAB
-- Server: 192.168.1.12

-- Crear base de datos si no existe
CREATE DATABASE DBLAB;

-- Conectar a la base de datos recién creada
\c DBLAB

-- Tabla 1: personas
-- Almacena la información personal de las personas (clientes, empleados)
CREATE TABLE IF NOT EXISTS personas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla 2: usuarios
-- Almacena la información de acceso y credenciales
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    idpersona INTEGER REFERENCES personas(id) ON DELETE CASCADE,
    userlogin VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar rendimiento de búsquedas
CREATE INDEX IF NOT EXISTS idx_personas_correo ON personas(correo);
CREATE INDEX IF NOT EXISTS idx_usuarios_userlogin ON usuarios(userlogin);

-- Comentarios para documentación
COMMENT ON TABLE personas IS 'Tabla principal de personas (clientes y empleados)';
COMMENT ON TABLE usuarios IS 'Tabla de credenciales de acceso del sistema';
COMMENT ON COLUMN personas.id IS 'Identificador único auto-generado';
COMMENT ON COLUMN personas.nombre IS 'Nombre de la persona';
COMMENT ON COLUMN personas.apellido IS 'Apellido de la persona';
COMMENT ON COLUMN personas.correo IS 'Correo electrónico único';
COMMENT ON COLUMN usuarios.id IS 'Identificador único auto-generado';
COMMENT ON COLUMN usuarios.idpersona IS 'Referencia al ID de la tabla personas';
COMMENT ON COLUMN usuarios.userlogin IS 'Nombre de usuario único para login';
