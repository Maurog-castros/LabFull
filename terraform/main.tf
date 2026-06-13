# Terraform Configuration for Practice Lab
# Author: Mauro
# Description: Infrastructure setup for FastAPI + PostgreSQL web application

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend local para guardar el estado
  backend "local" {
    path = "terraform/terraform.tfstate"
  }
}

# Provider local para ejecutar comandos y crear archivos
provider "local" {
  # Configuración específica si es necesaria
}

# Provider archive para empaquetar recursos si es necesario
provider "archive" {
  # Configuración específica si es necesaria
}

# Provider AWS para Ministack (192.168.1.12)
provider "aws" {
  region = var.aws_region

  # Usar variables de entorno o credenciales de AWS CLI
  # export AWS_ACCESS_KEY_ID="..."
  # export AWS_SECRET_ACCESS_KEY="..."
  # export AWS_DEFAULT_REGION="us-east-1"
}
