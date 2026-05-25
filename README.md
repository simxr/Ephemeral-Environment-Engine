# Ephemeral Environment Engine

EEE is a fully local preview-environment platform for Kubernetes workloads. The current foundation includes:

- a local K3d cluster with Traefik ingress enabled
- localhost port forwarding for HTTP and HTTPS
- a LocalStack container for free local AWS-compatible services
- a mono-repo layout for Terraform, Kubernetes, automation scripts, and CI
- Terragrunt-managed, PR-isolated LocalStack infrastructure state

## Prerequisites

Install these tools locally:

- Docker Desktop or Docker Engine
- k3d
- kubectl
- Docker Compose
- Terraform
- Terragrunt

## Start LocalStack

```sh
docker compose up -d localstack
```

LocalStack is exposed only on loopback:

- edge endpoint: `http://localhost:4566`
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

## Validate The Foundation

```sh
kubectl get nodes
kubectl get pods -A
docker compose ps
```

## Provision LocalStack Infrastructure

Milestone 2 adds Terraform and Terragrunt for mock AWS resources. Each PR environment lives in its own directory under `terraform/live/pr/<PR_NUMBER>` and writes isolated state to `terraform/.state/pr/<PR_NUMBER>/terraform.tfstate`.

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

## Local DNS

Future milestones will use per-PR hostnames such as:

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
