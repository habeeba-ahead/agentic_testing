// infra/patterns/templates/providers.tf
terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = ">= 5.0" }
  }
  # backend intentionally blank; the Stitch agent will configure it in an overlay
  backend "s3" {}
}

provider "aws" {
  region = var.region
}

variable "region"  { type = string }
variable "project" { type = string }
variable "env"     { type = string }
variable "tags"    { type = map(string) default = {} }
