terraform {
  required_version = ">= 1.6"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

# Auth: export GITHUB_TOKEN before running OpenTofu, e.g.
# GITHUB_TOKEN="$(gh auth token)".
provider "github" {
  owner = var.github_owner
}

# Client ID of the factory GitHub App. Not sensitive, so it is an Actions
# variable, read in the workflow as ${{ vars.FACTORY_APP_CLIENT_ID }}.
resource "github_actions_variable" "factory_app_client_id" {
  repository    = var.repository
  variable_name = "FACTORY_APP_CLIENT_ID"
  value         = var.factory_app_client_id
}

# Private key (.pem) of the factory GitHub App, read in the workflow as
# ${{ secrets.FACTORY_APP_PRIVATE_KEY }}. The provider encrypts it with the
# repo's public key before upload; the plaintext still lands in the state file.
resource "github_actions_secret" "factory_app_private_key" {
  repository      = var.repository
  secret_name     = "FACTORY_APP_PRIVATE_KEY"
  plaintext_value = file(var.factory_app_private_key_path)
}

# Optional: grant an already-installed app access to this repo. Skipped unless
# factory_app_installation_id is set. If you added the repo by hand when
# installing the app, leave it unset.
resource "github_app_installation_repository" "factory" {
  count = var.factory_app_installation_id == null ? 0 : 1

  installation_id = var.factory_app_installation_id
  repository      = var.repository
}

# Issue label used by the factory workflow trigger.
resource "github_issue_label" "factory_ready" {
  repository  = var.repository
  name        = "factory-ready"
  color       = "0e8a16"
  description = "Trigger the self-owned factory workflow"
}

# Issue label added when a factory run exhausts all retries.
resource "github_issue_label" "factory_failed" {
  repository  = var.repository
  name        = "factory-failed"
  color       = "d73a4a"
  description = "Factory run failed after exhausting retries"
}

# Branch protection applied to the default branch.
resource "github_branch_protection" "main" {
  repository_id = var.repository
  pattern       = "main"

  enforce_admins                = false
  required_linear_history      = false
  required_conversation_resolution = true
  allows_deletions             = false
  allows_force_pushes          = false

  required_status_checks {
    strict   = true
    contexts = ["test"]
  }

  required_pull_request_reviews {
    dismiss_stale_reviews            = true
    require_code_owner_reviews      = false
    required_approving_review_count = 1
  }
}

# Ensures the default GITHUB_TOKEN can create pull requests.
resource "github_workflow_repository_permissions" "default" {
  repository                       = var.repository
  default_workflow_permissions     = "write"
  can_approve_pull_request_reviews = true
}
