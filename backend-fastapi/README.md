# Backend FastAPI - LabFull

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
| POST | `/registrar` | Crear persona y usuario en una sola transacción |
| GET | `/personas/{id}` | Obtener persona por ID |

## Publicación

En el flujo de Minikube, el backend queda expuesto internamente por `backend-service` y el frontend lo consume vía `/api`.
