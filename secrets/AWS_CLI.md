# AWS CLI Configuration - DBLAB Lab

## 🇪🇸 Configuración de AWS CLI

### 1. Instalación

#### Windows (usando MSI)
```powershell
# Descargar e instalar AWS CLI v2
Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile "AWSCLIV2.msi"
Start-Process msiexec.exe -ArgumentList "/i AWSCLIV2.msi /qn" -Wait
```

#### Verificar instalación
```bash
aws --version
# aws-cli/2.x.x Python/3.x.x Windows/10
```

### 2. Configuración Inicial

#### Método A: Usando credenciales CSV (recomendado para laboratorio)
```bash
# Configurar perfil por defecto
aws configure

# Ingresar cuando se pida:
AWS Access Key ID [None]: TU_ACCESS_KEY_ID
AWS Secret Access Key [None]: TU_SECRET_ACCESS_KEY
Default region name [None]: us-east-1
Default output format [None]: json
```

#### Método B: Usando variables de entorno (recomendado para CI/CD)
```bash
# Configurar variables temporales
export AWS_ACCESS_KEY_ID="TU_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="TU_S...ort AWS_DEFAULT_REGION="us-east-1"

# O en Windows (PowerShell)
$env:AWS_ACCESS_KEY_ID="TU_ACCESS_KEY_ID"
$env:AWS_SECRET_ACCESS_KEY="TU_S...n### 3. Perfiles Múltiples

```bash
# Configurar perfil específico
aws configure --profile lab-profile

# Usar perfil específico en comandos
aws s3 ls --profile lab-profile
```

### 4. Verificación de Configuración

```bash
# Verificar credenciales
aws sts get-caller-identity

# Ver regiones disponibles
aws ec2 describe-regions

# Ver buckets S3 (si existen)
aws s3 ls
```

### 5. Comandos Útiles

| Comando | Descripción |
|---------|-------------|
| `aws configure` | Configurar credenciales y regiones |
| `aws sts get-caller-identity` | Ver identidad actual |
| `aws s3 ls` | Listar buckets S3 |
| `aws ec2 describe-instances` | Ver instancias EC2 |
| `aws iam list-users` | Listar usuarios IAM |

### 6. Uso con Terraform

```bash
# Terraform usará automáticamente las credenciales del AWS CLI
terraform init
terraform plan
terraform apply
```

### 7. Seguridad

⚠️ **Importante:**
- Nunca commitear archivos con credenciales reales
- Usar `terraform.tfvars.example` como plantilla
- Mantener archivos con credenciales reales en `.gitignore`
- Usar `secrets/` para archivos sensibles (ya ignorados)

---

## 🇺🇸 AWS CLI Configuration

### 1. Installation

#### Windows (using MSI)
```powershell
# Download and install AWS CLI v2
Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile "AWSCLIV2.msi"
Start-Process msiexec.exe -ArgumentList "/i AWSCLIV2.msi /qn" -Wait
```

#### Verify installation
```bash
aws --version
# aws-cli/2.x.x Python/3.x.x Windows/10
```

### 2. Initial Configuration

#### Method A: Using CSV credentials (recommended for lab)
```bash
# Configure default profile
aws configure

# Enter when prompted:
AWS Access Key ID [None]: YOUR_ACCESS_KEY_ID
AWS Secret Access Key [None]: YOUR_SECRET_ACCESS_KEY
Default region name [None]: us-east-1
Default output format [None]: json
```

#### Method B: Using environment variables (recommended for CI/CD)
```bash
# Configure temporary variables
export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="YOUR...ort AWS_DEFAULT_REGION="us-east-1"

# Or in Windows (PowerShell)
$env:AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY_ID"
$env:AWS_SECRET_ACCESS_KEY="YOUR...n### 3. Multiple Profiles

```bash
# Configure specific profile
aws configure --profile lab-profile

# Use specific profile in commands
aws s3 ls --profile lab-profile
```

### 4. Configuration Verification

```bash
# Verify credentials
aws sts get-caller-identity

# View available regions
aws ec2 describe-regions

# List S3 buckets (if any)
aws s3 ls
```

### 5. Useful Commands

| Command | Description |
|---------|-------------|
| `aws configure` | Configure credentials and regions |
| `aws sts get-caller-identity` | View current identity |
| `aws s3 ls` | List S3 buckets |
| `aws ec2 describe-instances` | View EC2 instances |
| `aws iam list-users` | List IAM users |

### 6. Usage with Terraform

```bash
# Terraform will automatically use AWS CLI credentials
terraform init
terraform plan
terraform apply
```

### 7. Security

⚠️ **Important:**
- Never commit files with real credentials
- Use `terraform.tfvars.example` as template
- Keep files with real credentials in `.gitignore`
- Use `secrets/` for sensitive files (already ignored)
