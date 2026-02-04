locals {
  lambda_sources_bucket_name = "${var.lambda_sources_bucket_prefix}-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

data "aws_caller_identity" "current" {}

resource "aws_lambda_code_signing_config" "dev" {
  description = "Code signing configuration for Lambda functions"

  allowed_publishers {
    signing_profile_version_arns = [
      aws_signer_signing_profile.dev.version_arn,
    ]
  }

  policies {
    untrusted_artifact_on_deployment = "Enforce" # Block deployments that fail code signing validation
  }

  tags = {
    Environment = "dev"
    Purpose     = "code-signing"
  }
}

resource "aws_signer_signing_profile" "dev" {
  platform_id = "AWSLambda-SHA384-ECDSA"

  tags = {
    Environment = "dev"
  }
}
