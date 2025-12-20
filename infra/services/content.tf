# ========================================
# Content Lambda function
# ========================================
resource "aws_lambda_function" "content_service" {
  function_name = "${var.project_name}-${var.environment}-content"
  role          = aws_iam_role.content_lambda.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 128

  s3_bucket = local.lambda_sources_bucket_name
  s3_key    = "content_service/content_service.zip"

  environment {
    variables = {
      ENVIRONMENT         = var.environment
      USERS_TABLE_NAME    = aws_dynamodb_table.users.name
      CONTENT_BUCKET_NAME = aws_s3_bucket.content.id
      CBTC_APP_URL        = var.app_url
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.content_lambda,
    aws_iam_role_policy_attachment.content_lambda_basic
  ]

  tags = {
    Name = "${var.project_name}-${var.environment}-content"
  }
}

# ========================================
# IAM permissions
# ========================================
# IAM role for content Lambda function
resource "aws_iam_role" "content_lambda" {
  name = "${var.project_name}-${var.environment}-content-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-content-lambda"
  }
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "content_lambda_basic" {
  role       = aws_iam_role.content_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM Policy for Content Lambda to Access S3
resource "aws_iam_role_policy" "content_lambda_s3" {
  name = "${var.project_name}-${var.environment}-content-s3"
  role = aws_iam_role.content_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.content.arn}/*"
      }
    ]
  })
}

# IAM Policy for DynamoDB Access
resource "aws_iam_role_policy" "content_lambda_dynamodb" {
  name = "${var.project_name}-${var.environment}-content-dynamodb"
  role = aws_iam_role.content_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Scan",
          "dynamodb:PutItem"
        ]
        Resource = aws_dynamodb_table.users.arn
      }
    ]
  })
}

# ========================================
# CloudWatch Log Group for content Lambda
# ========================================
resource "aws_cloudwatch_log_group" "content_lambda" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-content"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-${var.environment}-content-logs"
  }
}

# ========================================
# Content Bucket (S3)
# ========================================
resource "aws_s3_bucket" "content" {
  bucket = "${var.project_name}-${var.environment}-content-${data.aws_caller_identity.current.account_id}"

  # Force destroy for easier cleanup in dev/local
  force_destroy = var.environment == "local" ? true : false

  tags = {
    Name = "${var.project_name}-${var.environment}-content-${data.aws_caller_identity.current.account_id}"
  }
}
