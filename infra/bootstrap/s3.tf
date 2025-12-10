# Bucket for terraform state
locals {
  bucket_name = "cbtc-tfstate-${var.environment}"
}

resource "aws_s3_bucket" "terraform_state" {
  bucket = local.bucket_name

  tags = {
    Name = local.bucket_name
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_stat_access_block" {
  bucket = aws_s3_bucket.terraform_state.bucket

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "terraform_state_bucket_versioning" {
  bucket = aws_s3_bucket.terraform_state.bucket

  versioning_configuration {
    mfa_delete = "Enabled"
    status     = "Enabled"
  }
}
