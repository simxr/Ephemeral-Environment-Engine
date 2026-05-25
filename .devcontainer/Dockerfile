FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ARG KUBECTL_VERSION=v1.31.4
ARG K3D_VERSION=v5.7.4
ARG TERRAFORM_VERSION=1.10.3
ARG TERRAGRUNT_VERSION=v0.69.10
ARG HELM_VERSION=v3.16.3
ARG ARGOCD_VERSION=v2.13.2

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      bash-completion \
      ca-certificates \
      curl \
      dnsutils \
      jq \
      less \
      make \
      python3 \
      python3-pip \
      unzip \
    && rm -rf /var/lib/apt/lists/*

RUN ARCH="$(dpkg --print-architecture)" \
    && case "${ARCH}" in \
      amd64) BIN_ARCH=amd64 ;; \
      arm64) BIN_ARCH=arm64 ;; \
      *) echo "Unsupported architecture: ${ARCH}" >&2; exit 1 ;; \
    esac \
    && curl -fsSL -o /usr/local/bin/kubectl "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${BIN_ARCH}/kubectl" \
    && chmod +x /usr/local/bin/kubectl \
    && curl -fsSL -o /usr/local/bin/k3d "https://github.com/k3d-io/k3d/releases/download/${K3D_VERSION}/k3d-linux-${BIN_ARCH}" \
    && chmod +x /usr/local/bin/k3d \
    && curl -fsSL -o /tmp/terraform.zip "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_${BIN_ARCH}.zip" \
    && unzip -q /tmp/terraform.zip -d /usr/local/bin \
    && rm /tmp/terraform.zip \
    && curl -fsSL -o /usr/local/bin/terragrunt "https://github.com/gruntwork-io/terragrunt/releases/download/${TERRAGRUNT_VERSION}/terragrunt_linux_${BIN_ARCH}" \
    && chmod +x /usr/local/bin/terragrunt \
    && curl -fsSL -o /tmp/helm.tgz "https://get.helm.sh/helm-${HELM_VERSION}-linux-${BIN_ARCH}.tar.gz" \
    && tar -xzf /tmp/helm.tgz -C /tmp \
    && mv "/tmp/linux-${BIN_ARCH}/helm" /usr/local/bin/helm \
    && rm -rf /tmp/helm.tgz "/tmp/linux-${BIN_ARCH}" \
    && curl -fsSL -o /usr/local/bin/argocd "https://github.com/argoproj/argo-cd/releases/download/${ARGOCD_VERSION}/argocd-linux-${BIN_ARCH}" \
    && chmod +x /usr/local/bin/argocd

RUN kubectl completion bash >/etc/bash_completion.d/kubectl \
    && helm completion bash >/etc/bash_completion.d/helm \
    && k3d completion bash >/etc/bash_completion.d/k3d \
    && terragrunt --version >/dev/null \
    && terraform -install-autocomplete || true
