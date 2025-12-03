terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Configure remote backend (uncomment and configure as needed)
  # backend "s3" {
  #   bucket         = "cbtc-media-day-terraform-state"
  #   key            = "global/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "cbtc-media-day-terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "cbtc-media-day"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
