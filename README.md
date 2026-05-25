# Ephemeral Environment Engine

EEE is a fully local preview-environment platform for Kubernetes workloads. It provides:

- a local K3d cluster with Traefik ingress enabled
- localhost port forwarding for HTTP and HTTPS
- a LocalStack container for free local AWS-compatible services
- a mono-repo layout for Terraform, Kubernetes, automation scripts, and CI
- Terragrunt-managed, PR-isolated LocalStack infrastructure state
- Helm-based preview application deployment
- ArgoCD ApplicationSet automation for PR-scoped environments

## Prerequisites

Install these tools locally:

- Docker Desktop or Docker Engine
- k3d
- kubectl
- Docker Compose
- Terraform
- Terragrunt
- Helm
- ArgoCD CLI, optional for UI/login workflows

## Start LocalStack

```sh
docker compose up -d localstack
```

LocalStack is exposed on the local Docker host:

- host endpoint: `http://localhost:4566`
- in-cluster endpoint: `http://eee-localstack.default.svc.cluster.local:4566`
- enabled services: S3, DynamoDB, SQS, IAM

## Create The K3d Cluster

```sh
./scripts/create-k3d-cluster.sh
```

The script creates a multi-node K3d cluster named `eee` with Traefik enabled and maps:

- `http://localhost:80` to the cluster load balancer
- `https://localhost:443` to the cluster load balancer

You can override defaults:

```sh
CLUSTER_NAME=eee AGENTS=2 HTTP_PORT=80 HTTPS_PORT=443 ./scripts/create-k3d-cluster.sh
```

## Validate The Local Platform

```sh
kubectl get nodes
kubectl get pods -A
docker compose ps
```

## Provision LocalStack Infrastructure

Terraform and Terragrunt manage mock AWS resources for each preview environment. Each PR environment lives in its own directory under `terraform/live/pr/<PR_NUMBER>` and writes isolated state to `terraform/.state/pr/<PR_NUMBER>/terraform.tfstate`.

Example for PR #42:

```sh
cd terraform/live/pr/42
terragrunt init
terragrunt apply
```

Create another PR environment directory with:

```sh
./scripts/create-terraform-env.sh 43
```

This provisions local-only resources in LocalStack:

- S3 bucket for app data
- DynamoDB table for app state
- SQS queue for events
- least-privilege IAM policy mock for those resources

Destroy only that PR's resources:

```sh
cd terraform/live/pr/42
terragrunt destroy
```

## Bootstrap Preview Deployments

Install ArgoCD into the local K3d cluster and apply EEE's preview environment controllers:

```sh
./scripts/bootstrap-argocd.sh
```

The ApplicationSet watches GitHub pull requests from `pr/<number>` branches and creates an ArgoCD Application in an isolated namespace named `env-pr-<number>`.

Preview workloads are deployed from:

```text
kubernetes/charts/eee-preview-app
```

## Clean Up Stale Environments

Run the Janitor in dry-run mode:

```sh
python scripts/janitor.py
```

Delete stale namespaces and destroy their matching LocalStack infrastructure:

```sh
python scripts/janitor.py --apply
```

On Windows PowerShell:

```powershell
.\scripts\run-janitor.ps1 -Apply
```

The Janitor targets namespaces named `env-pr-<number>`. It removes environments when the matching GitHub PR is closed, merged, missing, or when the namespace is older than 24 hours. Set `GITHUB_TOKEN` or `GH_TOKEN` to avoid unauthenticated GitHub API limits.

## Local DNS

Preview environments use per-PR hostnames such as:

```text
pr42.local.dev
```

For early development, map individual hostnames in your hosts file:

```text
127.0.0.1 pr42.local.dev
```

Wildcard host routing requires dnsmasq, CoreDNS, Acrylic DNS Proxy, or another local DNS resolver because most hosts files do not support wildcard entries.

## Stop The Local Stack

```sh
k3d cluster delete eee
docker compose down
```

To remove LocalStack's persisted data as well:

```sh
docker compose down -v
```
