output "environment_name" {
  description = "Ephemeral environment identifier."
  value       = var.environment_name
}

output "s3_bucket_name" {
  description = "LocalStack S3 bucket for application data."
  value       = aws_s3_bucket.app_data.bucket
}

output "dynamodb_table_name" {
  description = "LocalStack DynamoDB table for application state."
  value       = aws_dynamodb_table.app_state.name
}

output "sqs_queue_url" {
  description = "LocalStack SQS queue URL for environment events."
  value       = aws_sqs_queue.events.url
}

output "iam_policy_arn" {
  description = "LocalStack IAM policy ARN for mock application access."
  value       = aws_iam_policy.app_mock_access.arn
}
