locals {
  normalized_environment = lower(replace(var.environment_name, "_", "-"))
  name_prefix            = "${local.normalized_environment}-${var.resource_suffix}"
  common_tags = {
    Project     = "eee"
    Environment = var.environment_name
    PullRequest = var.pr_number
    ManagedBy   = "terraform"
    Runtime     = "localstack"
  }
}

resource "aws_s3_bucket" "app_data" {
  bucket        = "${local.name_prefix}-app-data"
  force_destroy = true

  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "app_data" {
  bucket = aws_s3_bucket.app_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_dynamodb_table" "app_state" {
  name         = "${local.name_prefix}-app-state"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  tags = local.common_tags
}

resource "aws_sqs_queue" "events" {
  name = "${local.name_prefix}-events"

  tags = local.common_tags
}

resource "aws_iam_policy" "app_mock_access" {
  name        = "${local.name_prefix}-app-mock-access"
  description = "Least-privilege mock policy for ${var.environment_name} LocalStack resources."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:DeleteObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject"
        ]
        Resource = [
          aws_s3_bucket.app_data.arn,
          "${aws_s3_bucket.app_data.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:DeleteItem",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.app_state.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ReceiveMessage",
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.events.arn
      }
    ]
  })

  tags = local.common_tags
}
