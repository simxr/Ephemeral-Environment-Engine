locals {
  repo_root = get_repo_root()
}

remote_state {
  backend = "local"

  config = {
    path = "${local.repo_root}/terraform/.state/${path_relative_to_include()}/terraform.tfstate"
  }

  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"

  contents = <<EOF
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  skip_region_validation      = true

  endpoints {
    dynamodb = var.localstack_endpoint
    iam      = var.localstack_endpoint
    s3       = var.localstack_endpoint
    sqs      = var.localstack_endpoint
  }
}
EOF
}

inputs = {
  aws_region          = "us-east-1"
  localstack_endpoint = "http://localhost:4566"
}
