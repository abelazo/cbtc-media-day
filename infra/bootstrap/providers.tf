provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
  s3_use_path_style           = true

  endpoints {
    s3 = "http://localhost.localstack.cloud:4566"
  }

  default_tags {
    tags = {
      Project     = "cbtc-media-day"
      Environment = "local"
      ManagedBy   = "terraform"
    }
  }
}
