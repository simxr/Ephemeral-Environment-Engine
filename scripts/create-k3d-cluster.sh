#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-eee}"
HTTP_PORT="${HTTP_PORT:-80}"
HTTPS_PORT="${HTTPS_PORT:-443}"
AGENTS="${AGENTS:-2}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_command docker
require_command k3d
require_command kubectl

if k3d cluster list "$CLUSTER_NAME" >/dev/null 2>&1; then
  echo "K3d cluster '$CLUSTER_NAME' already exists."
  kubectl config use-context "k3d-${CLUSTER_NAME}" >/dev/null
else
  k3d cluster create "$CLUSTER_NAME" \
    --servers 1 \
    --agents "$AGENTS" \
    --api-port "127.0.0.1:6550" \
    --port "127.0.0.1:${HTTP_PORT}:80@loadbalancer" \
    --port "127.0.0.1:${HTTPS_PORT}:443@loadbalancer" \
    --wait
fi

kubectl config use-context "k3d-${CLUSTER_NAME}" >/dev/null
kubectl wait --for=condition=Ready nodes --all --timeout=120s

echo "K3d cluster '$CLUSTER_NAME' is ready."
echo "Traefik ingress is available through http://localhost:${HTTP_PORT} and https://localhost:${HTTPS_PORT}."
