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
