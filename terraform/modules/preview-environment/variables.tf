variable "pr_number" {
  description = "Pull request number used to isolate preview infrastructure."
  type        = string

  validation {
    condition     = can(regex("^[0-9]+$", var.pr_number))
    error_message = "pr_number must contain only digits."
  }
}

variable "environment_name" {
  description = "Stable ephemeral environment name, usually env-pr-<number>."
  type        = string

  validation {
    condition     = can(regex("^env-pr-[0-9]+$", var.environment_name))
    error_message = "environment_name must match env-pr-<number>."
  }
}

variable "aws_region" {
  description = "AWS region used by the LocalStack AWS provider."
  type        = string
  default     = "us-east-1"
}

variable "localstack_endpoint" {
  description = "LocalStack edge endpoint."
  type        = string
  default     = "http://localhost:4566"
}

variable "resource_suffix" {
  description = "Suffix appended to resource names to keep module resources grouped."
  type        = string
  default     = "local"
}
