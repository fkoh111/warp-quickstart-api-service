variable "github_owner" {
  type        = string
  description = "User or organization that owns the repository."
}

variable "repository" {
  type        = string
  description = "Repository name (without the owner) that runs the factory workflow."
}

variable "factory_app_client_id" {
  type        = string
  description = "Client ID of the factory GitHub App (shown on the app's settings page)."
}

variable "factory_app_private_key_path" {
  type        = string
  description = "Path to the .pem private key generated for the factory GitHub App. Keep it outside the repo."
}

variable "factory_app_installation_id" {
  type        = number
  default     = null
  description = "Optional. Installation ID of the app (the number in github.com/settings/installations/<id>). When set, OpenTofu also adds this repo to the installation."
}
