# Global Infrastructure
# This file contains shared resources used across all services

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# S3 bucket for Lambda source code
resource "aws_s3_bucket" "lambda_sources" {
  bucket = "lambda-sources-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "lambda-sources-${var.environment}"
  }
}

# Enable versioning for Lambda sources bucket
resource "aws_s3_bucket_versioning" "lambda_sources" {
  bucket = aws_s3_bucket.lambda_sources.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption for Lambda sources bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "lambda_sources" {
  bucket = aws_s3_bucket.lambda_sources.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
