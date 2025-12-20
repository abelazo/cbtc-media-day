locals {
  lambda_sources_bucket_name = "${var.lambda_sources_bucket_prefix}-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}
