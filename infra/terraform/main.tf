terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"   # le "plugin" qui sait parler à Docker
      version = "~> 3.0"
    }
  }
}

provider "docker" {
  host = "npipe:////./pipe/docker_engine"   # Docker Desktop sous Windows (Linux/Mac : unix:///var/run/docker.sock)
}

variable "postgres_password" {
  type      = string
  sensitive = true                        # Terraform ne l'affichera jamais dans les logs
}

resource "docker_network" "tenderiq" {
  name = "tenderiq-tf"
}

resource "docker_image" "postgres" {
  name = "postgres:16"
}

resource "docker_container" "postgres" {
  name  = "tf-tenderiq-postgres"
  image = docker_image.postgres.image_id   # référence à une autre ressource : Terraform gère l'ordre
  env   = ["POSTGRES_DB=tenderiq", "POSTGRES_USER=tenderiq", "POSTGRES_PASSWORD=${var.postgres_password}"]
  ports {
    internal = 5432
    external = 15432                      # port différent pour ne pas gêner Docker Compose
  }
  networks_advanced {
    name = docker_network.tenderiq.name
  }
}

resource "docker_image" "qdrant" {
  name = "qdrant/qdrant:v1.12.4"
}

resource "docker_container" "qdrant" {
  name  = "tf-tenderiq-qdrant"
  image = docker_image.qdrant.image_id
  ports {
    internal = 6333
    external = 16333
  }
  networks_advanced {
    name = docker_network.tenderiq.name
  }
}

output "postgres_port" {
  value = 15432
}

output "qdrant_url" {
  value = "http://localhost:16333"
}