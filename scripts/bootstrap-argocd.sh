#!/usr/bin/env bash
set -euo pipefail

ARGOCD_NAMESPACE="${ARGOCD_NAMESPACE:-argocd}"
ARGOCD_VERSION="${ARGOCD_VERSION:-stable}"
ARGOCD_MANIFEST_URL="https://raw.githubusercontent.com/argoproj/argo-cd/${ARGOCD_VERSION}/manifests/install.yaml"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_command kubectl

kubectl create namespace "$ARGOCD_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n "$ARGOCD_NAMESPACE" -f "$ARGOCD_MANIFEST_URL"
kubectl wait -n "$ARGOCD_NAMESPACE" --for=condition=Available deployment --all --timeout=300s
kubectl apply -k kubernetes/bootstrap

echo "ArgoCD is installed in namespace '${ARGOCD_NAMESPACE}'."
echo "Forward the API/UI locally with:"
echo "kubectl port-forward svc/argocd-server -n ${ARGOCD_NAMESPACE} 8080:443"
