# Variables for Terraform Configuration
# ======================================

variable "postgresql_host" {
  description = "PostgreSQL server IP address"
  type        = string
  default     = "192.168.1.12"
}

variable "postgresql_port" {
  description = "PostgreSQL server port"
  type        = number
  default     = 5432
}

variable "postgresql_database" {
  description = "Name of the PostgreSQL database to create"
  type        = string
  default     = "belleza_oriental"
}

variable "postgresql_username" {
  description = "PostgreSQL admin username"
  type        = string
}

variable "postgresql_password" {
  description = "PostgreSQL admin password"
  type        = string
  sensitive   = true
}

variable "app_environment" {
  description = "Application environment (dev, staging, prod)"
  type        = string
  default     = "development"
}

variable "backend_port" {
  description = "Port for FastAPI backend server"
  type        = number
  default     = 8000
}

variable "web_server_port" {
  description = "Port for static web server"
  type        = number
  default     = 8080
}

variable "aws_region" {
  description = "AWS region for infrastructure deployment"
  type        = string
  default     = "us-east-1"
}
