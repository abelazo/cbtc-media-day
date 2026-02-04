# Get current AWS account ID
data "aws_caller_identity" "current" {}

# S3 bucket for Lambda source code
resource "aws_s3_bucket" "lambda_sources" {
  bucket = "lambda-sources-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "lambda-sources-${var.environment}"
  }
}

resource "aws_s3_bucket_public_access_block" "lambda_sources" {
  bucket = aws_s3_bucket.lambda_sources.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "lambda_sources" {
  bucket = aws_s3_bucket.lambda_sources.id

  versioning_configuration {
    status = "Enabled"
  }
}
#trivy:ignore:AWS-0132
resource "aws_s3_bucket_server_side_encryption_configuration" "lambda_sources" {
  bucket = aws_s3_bucket.lambda_sources.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
