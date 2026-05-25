# EEE Devcontainer

This devcontainer carries the CLI toolchain needed to work on EEE without installing each tool on the host.

Included tools:

- Docker CLI and Docker Compose, connected to the host Docker engine
- k3d
- kubectl
- Helm
- Terraform
- Terragrunt
- ArgoCD CLI
- GitHub CLI
- Python 3

The host still needs Docker Desktop or another Docker engine because K3d and LocalStack run as Docker containers.

## Startup

Open the repository in VS Code or GitHub Codespaces and choose **Reopen in Container**.

After the container starts:

```sh
docker version
docker compose up -d localstack
./scripts/create-k3d-cluster.sh
./scripts/bootstrap-argocd.sh
```

The Kubernetes config is stored in the named volume `eee-kube` so it survives container rebuilds.
