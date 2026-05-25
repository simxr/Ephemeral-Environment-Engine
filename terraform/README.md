# Terraform And Terragrunt

Milestone 2 provisions local AWS-compatible resources in LocalStack with Terraform and Terragrunt.

The live layout is intentionally PR-scoped:

```text
terraform/live/pr/42/terragrunt.hcl
terraform/live/pr/43/terragrunt.hcl
```

Each PR directory gets its own local Terraform state file under:

```text
terraform/.state/pr/<PR_NUMBER>/terraform.tfstate
```

This keeps PR #42 from mutating or destroying PR #43's LocalStack resources.

## Prerequisites

- LocalStack running with `docker compose up -d localstack`
- Terraform
- Terragrunt

## Create A Preview Environment

```sh
cd terraform/live/pr/42
terragrunt init
terragrunt apply
```

Override generated values when needed:

```sh
terragrunt apply -var='aws_region=us-east-1'
```

## Destroy A Preview Environment

```sh
cd terraform/live/pr/42
terragrunt destroy
```

## LocalStack Provider Behavior

The generated AWS provider sends supported service traffic to `http://localhost:4566` and uses local-only placeholder credentials. It skips AWS account, metadata, credential, and region validation so no real AWS calls are required.
