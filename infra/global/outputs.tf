output "lambda_sources_bucket_name" {
  description = "Name of the Lambda sources S3 bucket"
  value       = aws_s3_bucket.lambda_sources.id
}

output "lambda_sources_bucket_arn" {
  description = "ARN of the Lambda sources S3 bucket"
  value       = aws_s3_bucket.lambda_sources.arn
}
