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
