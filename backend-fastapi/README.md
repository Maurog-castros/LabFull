# Backend FastAPI - DBLAB

## Instalación de dependencias
```bash
pip install -r requirements.txt
```

## Ejecutar el servidor
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Bienvenida y versión |
| GET | `/health` | Health check |
| POST | `/personas` | Crear persona |
| POST | `/usuarios` | Crear usuario |
| GET | `/personas/{id}` | Obtener persona por ID |
