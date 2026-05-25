# Ephemeral Environment Engine

EEE is a fully local preview-environment platform for Kubernetes workloads. Milestone 1 creates the foundation:

- a local K3d cluster with Traefik ingress enabled
- localhost port forwarding for HTTP and HTTPS
- a LocalStack container for free local AWS-compatible services
- a mono-repo layout for Terraform, Kubernetes, automation scripts, and CI

## Prerequisites

Install these tools locally:

- Docker Desktop or Docker Engine
- k3d
- kubectl
- Docker Compose

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
