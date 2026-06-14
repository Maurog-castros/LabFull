"""
Backend FastAPI para LabFull
============================
API para crear personas y usuarios en PostgreSQL.
"""

from base64 import b64encode
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from typing import Any, Dict, Generator
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

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

DEFAULT_STAGE_SUMMARIES: Dict[str, str] = {
    "Resolve Branch": "Valida la rama activa y bloquea ramas no soportadas.",
    "Checkout": "Descarga el repositorio y deja el commit listo para auditar.",
    "Validate Dependencies": "Comprueba Terraform, AWS CLI, Docker, SSH y kubectl.",
    "Terraform": "Verifica que Terraform esté disponible y usable en el agente.",
    "Platform Tools": "Revisa que las utilidades del runner estén instaladas.",
    "Build Inputs": "Enumera manifiestos, imágenes y artefactos que usa el pipeline.",
    "Deploy Minikube on Ubuntu": "Sincroniza y despliega FE, BE y BD en el Ubuntu con Minikube.",
    "Validate Reverse Proxy": "Confirma que la URL pública responde y que el backend está sano.",
    "Notify ClawCode for AWS": "Notifica a OpenClaw que el primer despliegue quedó listo para validación humana.",
    "Approve AWS Deployment": "Bloquea la promoción hasta recibir la señal 1.",
    "Deploy FE": "Publica el frontend en AWS.",
    "Deploy BE": "Publica el backend en AWS y lo prepara para usar RDS.",
    "Deploy BD": "Promueve la capa de datos hacia RDS y su migración.",
    "Notify ClawCode on AWS": "Notifica a OpenClaw que el despliegue final en AWS terminó.",
    "Main Branch Summary": "Deja main como rama de validación compartida.",
    "Approval Gate": "Exige la señal 1 antes de avanzar hacia AWS.",
    "Validate AWS Tooling": "Comprueba que el runner tiene las herramientas mínimas.",
}

DEFAULT_CONTAINER_CATALOG: list[Dict[str, Any]] = [
    {
        "id": "frontend",
        "name": "Frontend",
        "kind": "Deployment",
        "service": "frontend-service",
        "status": "published",
        "status_label": "Publicado",
        "replicas": "2 replicas",
        "ports": ["80/tcp"],
        "published": "Ingress: labfull.maurocastro.cl -> frontend-service:80",
        "purpose": "Sirve la interfaz web y concentra el acceso público al laboratorio.",
        "healthcheck": "GET /",
        "details": [
            "Imagen: labfull-frontend:minikube",
            "Lee el backend a través de /api en el reverse proxy.",
            "Es el punto de entrada público del stack en Minikube.",
        ],
    },
    {
        "id": "backend",
        "name": "Backend",
        "kind": "Deployment",
        "service": "backend-service",
        "status": "published",
        "status_label": "Publicado",
        "replicas": "2 replicas",
        "ports": ["8000/tcp"],
        "published": "Interno: backend-service:8000 -> /api del frontend",
        "purpose": "Expone la API FastAPI, registra personas y usuarios y consulta Jenkins.",
        "healthcheck": "GET /health",
        "details": [
            "Imagen: labfull-backend:minikube",
            "Conecta con PostgreSQL usando DB_HOST y DB_NAME desde el ConfigMap.",
            "Sirve /pipeline/latest y /containers/status para la UI.",
        ],
    },
    {
        "id": "postgres",
        "name": "PostgreSQL",
        "kind": "Deployment",
        "service": "postgres-service",
        "status": "stateful",
        "status_label": "Persistente",
        "replicas": "1 replica",
        "ports": ["5432/tcp"],
        "published": "Interno: postgres-service:5432",
        "purpose": "Almacena personas y usuarios del laboratorio.",
        "healthcheck": "pg_isready -U postgres",
        "details": [
            "Imagen: postgres:15-alpine",
            "En Minikube usa volume local para persistencia de laboratorio.",
            "Recibe credenciales desde app-secrets y variables del ConfigMap.",
        ],
    },
    {
        "id": "minikube",
        "name": "Minikube / Ingress",
        "kind": "Platform",
        "service": "labfull-ingress",
        "status": "routing",
        "status_label": "Ruteando",
        "replicas": "Cluster local",
        "ports": ["80/tcp"],
        "published": "labfull.maurocastro.cl -> frontend-service:80; /api -> backend-service:8000",
        "purpose": "Orquesta el despliegue local y publica la aplicación por el host público.",
        "healthcheck": "kubectl get ingress, svc, pods",
        "details": [
            "Host público: labfull.maurocastro.cl",
            "Ruta / entrega el frontend y /api se proxya al backend.",
            "La exposición del stack la determina el Ingress del namespace del laboratorio.",
        ],
    },
]


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


def _jenkins_settings() -> Dict[str, Any]:
    return {
        "base_url": os.getenv("JENKINS_BASE_URL", "https://jenkins.maurocastro.cl").rstrip("/"),
        "job_path": os.getenv("JENKINS_JOB_PATH", "job/LabFull-CI-CD").strip("/"),
        "user": os.getenv("JENKINS_USER", "").strip(),
        "api_token": os.getenv("JENKINS_API_TOKEN", "").strip(),
        "timeout": float(os.getenv("JENKINS_TIMEOUT_SECONDS", "8")),
    }


def _jenkins_url(*parts: str) -> str:
    settings = _jenkins_settings()
    clean_parts = [part.strip("/") for part in parts if part]
    return "/".join([settings["base_url"], *clean_parts])


def _jenkins_headers() -> Dict[str, str]:
    settings = _jenkins_settings()
    headers = {"Accept": "application/json"}
    if settings["user"] and settings["api_token"]:
        token = f'{settings["user"]}:{settings["api_token"]}'.encode("utf-8")
        headers["Authorization"] = f"Basic {b64encode(token).decode('ascii')}"
    return headers


def _fetch_jenkins_json(url: str) -> Dict[str, Any]:
    request = Request(url, headers=_jenkins_headers())
    settings = _jenkins_settings()
    with urlopen(request, timeout=settings["timeout"]) as response:
        payload = response.read().decode("utf-8")
    data = json.loads(payload)
    return data if isinstance(data, dict) else {}


def _format_timestamp_ms(timestamp_ms: Any) -> str | None:
    if timestamp_ms in (None, ""):
        return None
    try:
        timestamp = float(timestamp_ms) / 1000.0
    except (TypeError, ValueError):
        return None
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone()
    return dt.strftime("%d-%m-%y %H:%M:%S")


def _format_duration_ms(duration_ms: Any) -> str | None:
    if duration_ms in (None, ""):
        return None
    try:
        duration = float(duration_ms) / 1000.0
    except (TypeError, ValueError):
        return None
    if duration < 60:
        return f"{duration:.1f} s"
    minutes, seconds = divmod(int(duration), 60)
    return f"{minutes} min {seconds:02d} s"


def _normalize_stage_name(stage_name: str) -> str:
    return stage_name.strip()


def _stage_summary(stage_name: str, branch_name: str | None = None) -> str:
    normalized = _normalize_stage_name(stage_name)
    if normalized in DEFAULT_STAGE_SUMMARIES:
        return DEFAULT_STAGE_SUMMARIES[normalized]
    if branch_name == "minikube-deploy" and normalized == "Notify ClawCode":
        return "Notifica a OpenClaw que el primer despliegue quedó listo para validación humana."
    if branch_name == "aws-deploy" and normalized == "Notify ClawCode":
        return "Notifica a OpenClaw que el despliegue final en AWS terminó."
    return normalized


def _parse_branch_name(full_display_name: str | None) -> str | None:
    if not full_display_name:
        return None
    match = re.search(r"»\s*([^\s#]+)\s*#", full_display_name)
    if match:
        return match.group(1).strip()
    return None


def _stage_state(stage: Dict[str, Any]) -> str:
    status = str(stage.get("status") or "UNKNOWN").upper()
    return "success" if status in {"SUCCESS", "PASSED"} else status.lower()


def _parse_openclaw_state(build: Dict[str, Any], stages: list[Dict[str, Any]]) -> Dict[str, Any]:
    description = str(build.get("description") or "").lower()
    if "openclaw=sent" in description:
        return {
            "status": "sent",
            "label": "Enviado",
            "detail": "El pipeline marcó el envío a OpenClaw como completado.",
        }
    if "openclaw=skipped" in description:
        return {
            "status": "skipped",
            "label": "Omitido",
            "detail": "El webhook no estaba configurado en este build.",
        }
    if "openclaw=failed" in description:
        return {
            "status": "failed",
            "label": "Falló",
            "detail": "El envío a OpenClaw fue intentado, pero no terminó bien.",
        }

    notify_stage = next(
        (stage for stage in stages if "notify clawcode" in str(stage.get("name", "")).lower()),
        None,
    )
    if notify_stage:
        stage_status = str(notify_stage.get("status") or "").upper()
        if stage_status in {"SUCCESS", "PASSED"}:
            return {
                "status": "sent",
                "label": "Enviado",
                "detail": "La etapa de notificación terminó correctamente.",
            }
        if stage_status in {"NOT_EXECUTED", "SKIPPED"}:
            return {
                "status": "skipped",
                "label": "Omitido",
                "detail": "La notificación no se ejecutó en esta rama o no tenía webhook.",
            }
        if stage_status in {"FAILED", "FAILURE"}:
            return {
                "status": "failed",
                "label": "Falló",
                "detail": "La notificación a OpenClaw falló dentro de Jenkins.",
            }

    return {
        "status": "unknown",
        "label": "Desconocido",
        "detail": "Jenkins no expone una confirmación explícita del webhook en este build.",
    }


def _fallback_pipeline_payload(reason: str) -> Dict[str, Any]:
    branch = "minikube-deploy"
    stages = [
        {
            "name": name,
            "status": "unknown",
            "summary": _stage_summary(name, branch),
            "duration": None,
            "started_at": None,
            "finished_at": None,
        }
        for name in [
            "Resolve Branch",
            "Checkout",
            "Validate Dependencies",
            "Build Inputs",
            "Deploy Minikube on Ubuntu",
            "Validate Reverse Proxy",
            "Notify ClawCode for AWS",
        ]
    ]
    return {
        "source": "fallback",
        "status": "degraded",
        "error": reason,
        "job": {
            "name": os.getenv("JENKINS_JOB_NAME", "LabFull-CI-CD"),
            "path": os.getenv("JENKINS_JOB_PATH", "job/LabFull-CI-CD"),
            "url": _jenkins_url(os.getenv("JENKINS_JOB_PATH", "job/LabFull-CI-CD")),
        },
        "build": {
            "number": None,
            "result": "UNKNOWN",
            "started_at": None,
            "finished_at": None,
            "duration": None,
            "display_name": "No disponible",
            "url": None,
            "branch": branch,
        },
        "openclaw": {
            "status": "unknown",
            "label": "Desconocido",
            "detail": "No se pudo consultar Jenkins; el estado del webhook queda pendiente.",
        },
        "stages": stages,
        "summary": "El backend no logró leer Jenkins, pero mantiene un esquema de fallback para la UI.",
    }


def _build_pipeline_payload() -> Dict[str, Any]:
    settings = _jenkins_settings()
    job_path = settings["job_path"]
    build_tree = ",".join(
        [
            "number",
            "result",
            "building",
            "displayName",
            "fullDisplayName",
            "timestamp",
            "duration",
            "estimatedDuration",
            "url",
            "description",
            "actions[parameters[name,value]]",
        ]
    )
    build_url = _jenkins_url(job_path, "lastCompletedBuild", "api/json") + "?" + urlencode({"tree": build_tree})
    stages_url = _jenkins_url(job_path, "lastCompletedBuild", "wfapi", "describe")

    try:
        build = _fetch_jenkins_json(build_url)
        stages_payload = _fetch_jenkins_json(stages_url)
        raw_stages = stages_payload.get("stages") if isinstance(stages_payload, dict) else []
        if not isinstance(raw_stages, list):
            raw_stages = []

        branch_name = _parse_branch_name(str(build.get("fullDisplayName") or build.get("displayName") or "")) or "main"
        stages = []
        for stage in raw_stages:
            if not isinstance(stage, dict):
                continue
            start_ms = stage.get("startTimeMillis")
            duration_ms = stage.get("durationMillis")
            start = _format_timestamp_ms(start_ms)
            if start_ms in (None, "") or duration_ms in (None, ""):
                finished = None
            else:
                try:
                    finished = _format_timestamp_ms(float(start_ms) + float(duration_ms))
                except (TypeError, ValueError):
                    finished = None
            stages.append(
                {
                    "name": _normalize_stage_name(str(stage.get("name") or "Stage")),
                    "status": _stage_state(stage),
                    "summary": _stage_summary(str(stage.get("name") or "Stage"), branch_name),
                    "started_at": start,
                    "finished_at": finished,
                    "duration": _format_duration_ms(duration_ms),
                }
            )

        openclaw = _parse_openclaw_state(build, raw_stages)
        result = str(build.get("result") or "UNKNOWN").upper()
        started_at = _format_timestamp_ms(build.get("timestamp"))
        finished_at = None
        if build.get("timestamp") not in (None, "") and build.get("duration") not in (None, ""):
            try:
                finished_at = _format_timestamp_ms(float(build.get("timestamp")) + float(build.get("duration")))
            except (TypeError, ValueError):
                finished_at = None

        return {
            "source": "jenkins",
            "status": "success" if result == "SUCCESS" else result.lower(),
            "job": {
                "name": os.getenv("JENKINS_JOB_NAME", "LabFull-CI-CD"),
                "path": job_path,
                "url": _jenkins_url(job_path),
            },
            "build": {
                "number": build.get("number"),
                "result": result,
                "started_at": started_at,
                "finished_at": finished_at,
                "duration": _format_duration_ms(build.get("duration")),
                "display_name": build.get("fullDisplayName") or build.get("displayName") or f"#{build.get('number', 'N/A')}",
                "url": build.get("url"),
                "branch": branch_name,
            },
            "openclaw": openclaw,
            "stages": stages,
            "summary": f"Build {build.get('number')} en estado {result.lower()} para la rama {branch_name}.",
        }
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        return _fallback_pipeline_payload(str(exc))
    except Exception as exc:  # pragma: no cover - defensive fallback for Jenkins edge cases
        return _fallback_pipeline_payload(str(exc))


def _build_container_payload() -> Dict[str, Any]:
    containers = [dict(container) for container in DEFAULT_CONTAINER_CATALOG]
    return {
        "source": "inventory",
        "status": "ready",
        "title": "Estado de containers y publicación",
        "summary": "Topología de frontend, backend, PostgreSQL y Minikube/Ingress del laboratorio.",
        "selected_id": "minikube",
        "containers": containers,
    }


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


@app.get("/pipeline/latest")
async def latest_pipeline() -> Dict[str, Any]:
    return _build_pipeline_payload()


@app.get("/containers/status")
async def containers_status() -> Dict[str, Any]:
    return _build_container_payload()


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
