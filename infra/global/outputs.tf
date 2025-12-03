output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.arn
}

output "app_data_bucket_name" {
  description = "Name of the application data S3 bucket"
  value       = aws_s3_bucket.app_data.id
}

output "app_data_bucket_arn" {
  description = "ARN of the application data S3 bucket"
  value       = aws_s3_bucket.app_data.arn
}

output "log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.app_logs.name
}
