"""
Backend FastAPI para LabFull
============================
API para crear personas y usuarios en PostgreSQL.
"""

from contextlib import contextmanager
from typing import Any, Dict, Generator
import os
import re

import psycopg2
from psycopg2 import errors
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field


app = FastAPI(
    title="DBLAB API",
    description="Backend para laboratorio práctico de Terraform",
    version="1.1.0",
)


class PersonaCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    correo: str = Field(min_length=5, max_length=255)


class UsuarioCreate(BaseModel):
    idpersona: int = Field(gt=0)
    userlogin: str = Field(min_length=3, max_length=100)


class RegistroCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    username: str = Field(min_length=3, max_length=100)


def _db_settings() -> Dict[str, Any]:
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "DBLAB"),
        "user": os.getenv("DB_USER", os.getenv("POSTGRES_USER", "postgres")),
        "password": os.getenv("DB_PASSWORD", os.getenv("POSTGRES_PASSWORD", "password123")),
        "connect_timeout": 5,
    }


@contextmanager
def _db_connection() -> Generator[Any, None, None]:
    conn = psycopg2.connect(**_db_settings())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_schema() -> None:
    ddl = """
    CREATE TABLE IF NOT EXISTS personas (
        id SERIAL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        apellido VARCHAR(100) NOT NULL,
        correo VARCHAR(255) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        idpersona INTEGER REFERENCES personas(id) ON DELETE CASCADE,
        userlogin VARCHAR(100) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_personas_correo ON personas(correo);
    CREATE INDEX IF NOT EXISTS idx_usuarios_userlogin ON usuarios(userlogin);
    """

    with _db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)


def _normalize_username(username: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "", username.strip().lower())
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username inválido")
    return cleaned


def _build_correo(username: str) -> str:
    return f"{_normalize_username(username)}@dblab.local"


def _insert_persona(cur: Any, nombre: str, apellido: str, correo: str) -> int:
    cur.execute(
        """
        INSERT INTO personas (nombre, apellido, correo)
        VALUES (%s, %s, %s)
        RETURNING id, nombre, apellido, correo, created_at
        """,
        (nombre.strip(), apellido.strip(), correo),
    )
    row = cur.fetchone()
    return int(row["id"])


def _insert_usuario(cur: Any, idpersona: int, userlogin: str) -> None:
    cur.execute(
        """
        INSERT INTO usuarios (idpersona, userlogin)
        VALUES (%s, %s)
        """,
        (idpersona, _normalize_username(userlogin)),
    )


def _fetch_persona(cur: Any, persona_id: int) -> Dict[str, Any] | None:
    cur.execute(
        """
        SELECT id, nombre, apellido, correo, created_at
        FROM personas
        WHERE id = %s
        """,
        (persona_id,),
    )
    row = cur.fetchone()
    return dict(row) if row else None


@app.on_event("startup")
async def startup_event() -> None:
    try:
        _ensure_schema()
    except Exception:
        # El backend sigue levantando para que healthchecks y la UI no se rompan
        pass


@app.get("/")
async def root() -> Dict[str, str]:
    return {
        "message": "Bienvenido a DBLAB API",
        "version": "1.1.0",
        "status": "operativo",
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    try:
        with _db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {"status": "healthy", "database": "up"}
    except Exception:
        return {"status": "degraded", "database": "down"}


@app.post("/personas", status_code=status.HTTP_201_CREATED)
async def crear_persona(persona: PersonaCreate) -> Dict[str, Any]:
    correo = persona.correo.strip().lower()
    try:
        with _db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                persona_id = _insert_persona(cur, persona.nombre, persona.apellido, correo)
        return {
            "message": "Persona creada exitosamente",
            "data": {
                "id": persona_id,
                "nombre": persona.nombre.strip(),
                "apellido": persona.apellido.strip(),
                "correo": correo,
            },
        }
    except errors.UniqueViolation as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Correo ya registrado") from exc


@app.post("/usuarios", status_code=status.HTTP_201_CREATED)
async def crear_usuario(usuario: UsuarioCreate) -> Dict[str, Any]:
    try:
        with _db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT 1 FROM personas WHERE id = %s", (usuario.idpersona,))
                if cur.fetchone() is None:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona no encontrada")
                _insert_usuario(cur, usuario.idpersona, usuario.userlogin)
        return {
            "message": "Usuario creado exitosamente",
            "data": {
                "idpersona": usuario.idpersona,
                "userlogin": _normalize_username(usuario.userlogin),
            },
        }
    except errors.UniqueViolation as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuario ya registrado") from exc


@app.post("/registrar", status_code=status.HTTP_201_CREATED)
async def registrar_persona_y_usuario(registro: RegistroCreate) -> Dict[str, Any]:
    correo = _build_correo(registro.username)
    try:
        with _db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO personas (nombre, apellido, correo)
                    VALUES (%s, %s, %s)
                    RETURNING id, nombre, apellido, correo, created_at
                    """,
                    (registro.nombre.strip(), registro.apellido.strip(), correo),
                )
                persona = cur.fetchone()
                if persona is None:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo crear la persona")

                cur.execute(
                    """
                    INSERT INTO usuarios (idpersona, userlogin)
                    VALUES (%s, %s)
                    RETURNING id, idpersona, userlogin, created_at
                    """,
                    (persona["id"], _normalize_username(registro.username)),
                )
                usuario = cur.fetchone()

        return {
            "message": "Registro creado exitosamente",
            "data": {
                "persona": dict(persona),
                "usuario": dict(usuario) if usuario else None,
            },
        }
    except errors.UniqueViolation as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un registro con ese correo o username",
        ) from exc


@app.get("/personas/{persona_id}")
async def obtener_persona(persona_id: int) -> Dict[str, Any]:
    if persona_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID inválido")

    with _db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            persona = _fetch_persona(cur, persona_id)

    if persona is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona no encontrada")

    return persona
