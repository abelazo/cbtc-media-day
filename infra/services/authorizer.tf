# Authorizer Lambda ###########################################################
resource "aws_lambda_function" "authorizer" {
  #checkov:skip=CKV_AWS_50:No need to enable X-Ray
  #checkov:skip=CKV_AWS_116:No need for DLQ
  #checkov:skip=CKV_AWS_117:It is OK to be in VPC without NAT for this function
  #checkov:skip=CKV_AWS_173:No need to encrypt environment variables

  function_name = "${var.project_name}-${var.environment}-authorizer"
  role          = aws_iam_role.authorizer_lambda.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 30
  memory_size   = 128

  reserved_concurrent_executions = -1

  s3_bucket               = local.lambda_sources_bucket_name
  s3_key                  = "authorizer/authorizer.zip"
  code_signing_config_arn = aws_lambda_code_signing_config.dev.arn

  environment {
    variables = {
      ENVIRONMENT      = var.environment
      USERS_TABLE_NAME = aws_dynamodb_table.users.name
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

resource "aws_iam_role_policy_attachment" "authorizer_lambda_basic" {
  role       = aws_iam_role.authorizer_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

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

# CloudWatch Log Group for authorizer Lambda ##################################
resource "aws_cloudwatch_log_group" "authorizer_lambda" {
  #checkov:skip=CKV_AWS_158:AWS-manged key is acceptable
  #checkov:skip=CKV_AWS_338:30 days retention is acceptable

  name              = "/aws/lambda/${var.project_name}-${var.environment}-authorizer"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-${var.environment}-authorizer-logs"
  }
}

# DynamoDB Table for Users ####################################################
resource "aws_dynamodb_table" "users" {
  #checkov:skip=CKV_AWS_28:No backup is acceptable for this table as it only contains non-critical user data that can be recreated if needed
  #checkov:skip=CKV_AWS_119:AWS-managed encryption is acceptable

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
