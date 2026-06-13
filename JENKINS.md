# Jenkins Pipeline - DBLAB Lab

## Estructura del Pipeline

El Jenkinsfile define 6 etapas:

1. **Checkout** - Recupera el código del repositorio
2. **Validate Terraform** - Valida y formatea la infraestructura
3. **Database Setup** - Configura PostgreSQL (DBLAB)
4. **Setup Backend** - Prepara entorno Python/FastAPI
5. **Setup Frontend** - Verifica archivos web
6. **Run Tests** - Ejecuta validaciones
7. **Build Documentation** - Genera reporte de progreso

## Uso

1. Crear nuevo job en Jenkins tipo "Pipeline"
2. Apuntar al repositorio Git
3. Usar `Jenkinsfile` como script de pipeline
4. Ejecutar build

## Variables de Entorno

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `DB_HOST` | 192.168.1.12 | Servidor PostgreSQL |
| `DB_NAME` | DBLAB | Nombre base de datos |
| `BACKEND_PORT` | 8000 | Puerto FastAPI |
| `WEB_PORT` | 8080 | Puerto Web |
