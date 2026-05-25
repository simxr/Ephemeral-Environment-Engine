# Kubernetes

Kubernetes manifests are split into:

- `bootstrap`: ArgoCD and ApplicationSet configuration for preview environments
- `charts`: Helm charts deployed into each ephemeral namespace

## Bootstrap ArgoCD

Create the cluster first:

```sh
./scripts/create-k3d-cluster.sh
```

Install ArgoCD and the ApplicationSet controller:

```sh
./scripts/bootstrap-argocd.sh
```

Apply the preview environment bootstrap manifests:

```sh
kubectl apply -k kubernetes/bootstrap
```

## Preview App Chart

Render a local preview for PR #42:

```sh
helm template env-pr-42 kubernetes/charts/eee-preview-app \
  --namespace env-pr-42 \
  --set prNumber=42
```

The chart injects LocalStack settings into the workload and creates an ingress host at `pr42.local.dev`.
