# ========================================
# Authorizer Lambda
# ========================================
# Authorizer Lambda function
resource "aws_lambda_function" "authorizer" {
  function_name = "${var.project_name}-${var.environment}-authorizer"
  role          = aws_iam_role.authorizer_lambda.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 128

  s3_bucket = local.lambda_sources_bucket_name
  s3_key    = "authorizer/authorizer.zip"

  environment {
    variables = {
      ENVIRONMENT         = var.environment
      USERS_TABLE_NAME    = aws_dynamodb_table.users.name
      CONTENT_BUCKET_NAME = "${var.project_name}-${var.environment}-content"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.authorizer_lambda,
    aws_iam_role_policy_attachment.authorizer_lambda_basic
  ]

  tags = {
    Name = "${var.project_name}-${var.environment}-authorizer"
  }
}

# ========================================
# IAM role for authorizer Lambda function
# ========================================
resource "aws_iam_role" "authorizer_lambda" {
  name = "${var.project_name}-${var.environment}-authorizer-lambda"

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
    Name = "${var.project_name}-${var.environment}-authorizer-lambda"
  }
}

# Attach basic Lambda execution policy to authorizer
resource "aws_iam_role_policy_attachment" "authorizer_lambda_basic" {
  role       = aws_iam_role.authorizer_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM Policy for authorizer Lambda to access DynamoDB
resource "aws_iam_role_policy" "authorizer_lambda_dynamodb" {
  name = "${var.project_name}-${var.environment}-authorizer-dynamodb"
  role = aws_iam_role.authorizer_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem"
        ]
        Resource = aws_dynamodb_table.users.arn
      }
    ]
  })
}

# ========================================
# CloudWatch Log Group for authorizer Lambda
# ========================================
resource "aws_cloudwatch_log_group" "authorizer_lambda" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-authorizer"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-${var.environment}-authorizer-logs"
  }
}

# ========================================
# DynamoDB Table for Users
# ========================================
# DynamoDB Table for Users
resource "aws_dynamodb_table" "users" {
  name         = "users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "username"

  attribute {
    name = "username"
    type = "S"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-users"
  }
}
