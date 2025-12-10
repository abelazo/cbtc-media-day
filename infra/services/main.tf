# Services Infrastructure
# This file contains infrastructure for individual Lambda services

locals {
  lambda_sources_bucket_name = "${var.lambda_sources_bucket_prefix}-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}


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

# CloudWatch Log Group for content Lambda
resource "aws_cloudwatch_log_group" "content_lambda" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-content"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-${var.environment}-content-logs"
  }
}

# Content Lambda function
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
      ENVIRONMENT = var.environment
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

# API Gateway REST API
resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.project_name}-${var.environment}-api"
  description = "API Gateway for ${var.project_name}"

  tags = {
    Name = "${var.project_name}-${var.environment}-api"
  }
}

# API Gateway resource for /content
resource "aws_api_gateway_resource" "content" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "content"
}

# API Gateway GET method for /content
resource "aws_api_gateway_method" "content_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.content.id
  http_method   = "GET"
  authorization = "NONE"
}

# Lambda integration for GET /content
resource "aws_api_gateway_integration" "content_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.content.id
  http_method             = aws_api_gateway_method.content_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.content_service.invoke_arn
}

# Lambda permission for API Gateway to invoke
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.content_service.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# API Gateway deployment
resource "aws_api_gateway_deployment" "v1" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.content.id,
      aws_api_gateway_method.content_get.id,
      aws_api_gateway_integration.content_lambda.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.content_lambda
  ]
}

# API Gateway stage v1
resource "aws_api_gateway_stage" "v1" {
  deployment_id = aws_api_gateway_deployment.v1.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = "v1"

  tags = {
    Name = "${var.project_name}-${var.environment}-v1"
  }
}
