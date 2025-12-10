variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "cbtc-media-day"
}

variable "lambda_sources_bucket_name" {
  description = "Name of the S3 bucket containing Lambda source code"
  type        = string
  default     = "lambda-sources-local-000000000000"
}
