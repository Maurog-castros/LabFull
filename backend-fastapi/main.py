"""
Backend FastAPI para Laboratorio Terraform
==========================================
Aplicación básica con endpoints de prueba
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# Configuración de la aplicación
app = FastAPI(
    title="DBLAB API",
    description="Backend para laboratorio práctico de Terraform",
    version="1.0.0"
)

# Modelos Pydantic para validación
class PersonaCreate(BaseModel):
    nombre: str
    apellido: str
    correo: str

class UsuarioCreate(BaseModel):
    idpersona: int
    userlogin: str


# Endpoints básicos
@app.get("/")
async def root():
    """Endpoint raíz de bienvenida"""
    return {
        "message": "Bienvenido a DBLAB API",
        "version": "1.0.0",
        "status": "operativo"
    }


@app.get("/health")
async def health_check():
    """Health check para verificación de estado"""
    return {"status": "healthy", "database": "pendiente"}


@app.post("/personas")
async def crear_persona(persona: PersonaCreate):
    """Crear una nueva persona"""
    return {
        "message": "Persona creada exitosamente",
        "data": persona.dict()
    }


@app.post("/usuarios")
async def crear_usuario(usuario: UsuarioCreate):
    """Crear un nuevo usuario"""
    return {
        "message": "Usuario creado exitosamente",
        "data": usuario.dict()
    }


@app.get("/personas/{persona_id}")
async def obtener_persona(persona_id: int):
    """Obtener una persona por ID"""
    if persona_id <= 0:
        raise HTTPException(status_code=400, detail="ID inválido")
    return {
        "id": persona_id,
        "nombre": "Ejemplo",
        "apellido": "Apellido",
        "correo": "ejemplo@dominio.com"
    }
