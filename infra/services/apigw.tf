# API Gateway #################################################################
resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.project_name}-${var.environment}-api"
  description = "API Gateway for ${var.project_name}"

  lifecycle {
    create_before_destroy = true
  }

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

# API Gateway Authorizer
resource "aws_api_gateway_authorizer" "lambda_authorizer" {
  name                   = "${var.project_name}-${var.environment}-authorizer"
  rest_api_id            = aws_api_gateway_rest_api.main.id
  authorizer_uri         = aws_lambda_function.authorizer.invoke_arn
  authorizer_credentials = aws_iam_role.authorizer_invocation.arn
  type                   = "TOKEN"
  identity_source        = "method.request.header.Authorization"
}

# IAM role for API Gateway to invoke authorizer
resource "aws_iam_role" "authorizer_invocation" {
  name = "${var.project_name}-${var.environment}-authorizer-invocation"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for API Gateway to invoke authorizer Lambda
resource "aws_iam_role_policy" "authorizer_invocation" {
  name = "${var.project_name}-${var.environment}-authorizer-invocation"
  role = aws_iam_role.authorizer_invocation.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = aws_lambda_function.authorizer.arn
      }
    ]
  })
}

# API Gateway GET method for /content
resource "aws_api_gateway_method" "content_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.content.id
  http_method   = "GET"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.lambda_authorizer.id
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

resource "aws_api_gateway_deployment" "v1" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.content.id,
      aws_api_gateway_method.content_get.id,
      aws_api_gateway_integration.content_lambda.id,
      aws_api_gateway_authorizer.lambda_authorizer.id,
      aws_api_gateway_method.content_options.id,
      aws_api_gateway_integration.content_options.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.content_lambda
  ]
}


resource "aws_api_gateway_stage" "v1" {
  #checkov:skip=CKV_AWS_73:Not activating X-Ray for cost reasons
  #checkov:skip=CKV_AWS_76:Not activating access logging for cost reasons
  #checkov:skip=CKV_AWS_120:Not activating Catching for cost reasons

  deployment_id = aws_api_gateway_deployment.v1.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = "v1"

  tags = {
    Name = "${var.project_name}-${var.environment}-v1"
  }
}
