#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <pr-number>" >&2
  exit 1
fi

PR_NUMBER="$1"

if ! [[ "$PR_NUMBER" =~ ^[0-9]+$ ]]; then
  echo "PR number must contain only digits." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${REPO_ROOT}/terraform/live/pr/${PR_NUMBER}"
TARGET_FILE="${TARGET_DIR}/terragrunt.hcl"

mkdir -p "$TARGET_DIR"

if [ -f "$TARGET_FILE" ]; then
  echo "Terragrunt environment already exists: ${TARGET_FILE}"
  exit 0
fi

cat >"$TARGET_FILE" <<'TERRAGRUNT'
include "root" {
  path = find_in_parent_folders("terragrunt.hcl")
}

locals {
  pr_number        = basename(get_terragrunt_dir())
  environment_name = "env-pr-${local.pr_number}"
}

terraform {
  source = "../../../modules/preview-environment"
}

inputs = {
  pr_number        = local.pr_number
  environment_name = local.environment_name
}
TERRAGRUNT

echo "Created ${TARGET_FILE}"
