# LabFull

Practical lab to train skills with Terraform, FastAPI and PostgreSQL.

## 🇪🇸 Descripción del Proyecto

Laboratorio práctico para entrenar habilidades con Terraform, FastAPI y PostgreSQL.

### 🏗️ Estructura del Proyecto

```
Terraform/
├── app-web/              # Frontend HTML/CSS (Cyberpunk Login)
│   ├── index.html        # Interfaz de login moderna
│   └── README.md         # Documentación del frontend
├── backend-fastapi/      # Backend Python FastAPI
│   ├── main.py           # Aplicación FastAPI con endpoints
│   ├── requirements.txt  # Dependencias de Python
│   └── README.md         # Documentación del backend
├── bd/                   # Scripts PostgreSQL
│   ├── init-db.sql       # Script de inicialización (tablas personas, usuarios)
│   └── .env.example      # Ejemplo de variables de entorno
├── terraform/            # Infrastructure as Code (Terraform)
│   ├── main.tf           # Configuración principal
│   ├── variables.tf      # Variables definidas
│   └── terraform.tfvars.example  # Ejemplo de variables
└── README.md            # Este archivo / This file
```

### 🚀 Características

| Componente | Descripción |
|------------|-------------|
| **Frontend** | Login cyberpunk con animaciones modernas, validación de usuario |
| **Backend** | FastAPI con endpoints para personas y usuarios |
| **Base de Datos** | PostgreSQL (DBLAB) con tablas `personas` y `usuarios` |
| **Infraestructura** | Terraform para gestión de recursos |

### 🚀 Flujo de despliegue

1. `main`: validación compartida y higiene de merge.
2. `minikube-deploy`: sincronización y despliegue en Ubuntu con Minikube.
3. Validación técnica: comprobación del Ingress y del reverse proxy del servidor.
4. Validación manual: el agente recibe aprobación por WhatsApp.
5. `aws-deploy`: promoción a AWS con FE, BE y RDS.
6. GitHub Actions puede disparar el branch `minikube-deploy` en Jenkins desde un runner `self-hosted`.

### 📊 Estructura de Base de Datos

**Tabla `personas`:**
- `id` - SERIAL PRIMARY KEY
- `nombre` - VARCHAR(100) NOT NULL
- `apellido` - VARCHAR(100) NOT NULL  
- `correo` - VARCHAR(255) UNIQUE NOT NULL
- `created_at` - TIMESTAMP DEFAULT CURRENT_TIMESTAMP

**Tabla `usuarios`:**
- `id` - SERIAL PRIMARY KEY
- `idpersona` - INTEGER REFERENCES personas(id) ON DELETE CASCADE
- `userlogin` - VARCHAR(100) UNIQUE NOT NULL
- `created_at` - TIMESTAMP DEFAULT CURRENT_TIMESTAMP

### 🛠️ Requisitos Previos

- Terraform >= 1.0.0
- Python 3.8+ y pip
- PostgreSQL client (psql)
- Servidor PostgreSQL en `192.168.1.12`

### 📝 Instrucciones de Instalación

#### 1. Configurar Base de Datos PostgreSQL
```bash
psql -h 192.168.1.12 -U <usuario> -f bd/init-db.sql
```

#### 2. Configurar Backend FastAPI
```bash
cd backend-fastapi
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Ejecutar Frontend
```bash
cd app-web
python -m http.server 8080
# Acceder a: http://localhost:8080
```

### 📈 Progreso del Laboratorio

| Paso | Estado | Commit |
|------|--------|--------|
| 1. Estructura de carpetas | ✅ Completado | `04e9cc5` |
| 2. Configuración Terraform | ✅ Completado | `06d2aa4` |
| 3. Script PostgreSQL | ✅ Completado | `06d2aa4` |
| 4. Backend FastAPI | ✅ Completado | `06d2aa4` |
| 5. Interfaz Login Cyberpunk | ✅ Completado | `8b008c0` |
| 6. Documentación | 🔄 En progreso | - |

### 🔗 Endpoints del Backend

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Bienvenida y versión |
| GET | `/health` | Health check |
| POST | `/personas` | Crear persona |
| POST | `/usuarios` | Crear usuario |
| GET | `/personas/{id}` | Obtener persona por ID |

---

## 🇺🇸 Project Description

Practical lab to train skills with Terraform, FastAPI and PostgreSQL.

### 🏗️ Project Structure

```
Terraform/
├── app-web/              # Frontend HTML/CSS (Cyberpunk Login)
│   ├── index.html        # Modern login interface
│   └── README.md         # Frontend documentation
├── backend-fastapi/      # Python FastAPI Backend
│   ├── main.py           # FastAPI application with endpoints
│   ├── requirements.txt  # Python dependencies
│   └── README.md         # Backend documentation
├── bd/                   # PostgreSQL Scripts
│   ├── init-db.sql       # Database initialization script (personas, usuarios tables)
│   └── .env.example      # Environment variables example
├── terraform/            # Infrastructure as Code (Terraform)
│   ├── main.tf           # Main configuration
│   ├── variables.tf      # Defined variables
│   └── terraform.tfvars.example  # Variables example
└── README.md            # This file / Este archivo
```

### 🚀 Features

| Component | Description |
|-----------|-------------|
| **Frontend** | Cyberpunk login with modern animations, user validation |
| **Backend** | FastAPI with endpoints for personas and usuarios |
| **Database** | PostgreSQL (DBLAB) with `personas` and `usuarios` tables |
| **Infrastructure** | Terraform for resource management |

### 📊 Database Structure

**Table `personas`:**
- `id` - SERIAL PRIMARY KEY
- `nombre` - VARCHAR(100) NOT NULL
- `apellido` - VARCHAR(100) NOT NULL  
- `correo` - VARCHAR(255) UNIQUE NOT NULL
- `created_at` - TIMESTAMP DEFAULT CURRENT_TIMESTAMP

**Table `usuarios`:**
- `id` - SERIAL PRIMARY KEY
- `idpersona` - INTEGER REFERENCES personas(id) ON DELETE CASCADE
- `userlogin` - VARCHAR(100) UNIQUE NOT NULL
- `created_at` - TIMESTAMP DEFAULT CURRENT_TIMESTAMP

### 🛠️ Prerequisites

- Terraform >= 1.0.0
- Python 3.8+ and pip
- PostgreSQL client (psql)
- PostgreSQL server at `192.168.1.12`

### 📝 Installation Instructions

#### 1. Configure PostgreSQL Database
```bash
psql -h 192.168.1.12 -U <username> -f bd/init-db.sql
```

#### 2. Configure FastAPI Backend
```bash
cd backend-fastapi
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Run Frontend
```bash
cd app-web
python -m http.server 8080
# Access at: http://localhost:8080
```

### 📈 Lab Progress

| Step | Status | Commit |
|------|--------|--------|
| 1. Folder structure | ✅ Completed | `04e9cc5` |
| 2. Terraform setup | ✅ Completed | `06d2aa4` |
| 3. PostgreSQL script | ✅ Completed | `06d2aa4` |
| 4. FastAPI Backend | ✅ Completed | `06d2aa4` |
| 5. Cyberpunk Login UI | ✅ Completed | `8b008c0` |
| 6. Documentation | 🔄 In progress | - |

### 🔗 Backend Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome and version |
| GET | `/health` | Health check |
| POST | `/personas` | Create persona |
| POST | `/usuarios` | Create usuario |
| GET | `/personas/{id}` | Get persona by ID |

---

## 📝 Git History

Para auditar el progreso del laboratorio:
```bash
git log --oneline
```
