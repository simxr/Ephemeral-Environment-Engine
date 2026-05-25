#!/usr/bin/env bash
set -euo pipefail

mkdir -p "${HOME}/.kube"
touch "${HOME}/.kube/config"

cat <<'EOF'
EEE devcontainer is ready.

Installed tools:
EOF

docker --version || true
docker compose version || true
k3d version || true
kubectl version --client=true || true
helm version --short || true
terraform version || true
terragrunt --version || true
argocd version --client || true
gh --version || true
