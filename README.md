# Warp Quickstart API Service

[![Factory issue labeled](https://github.com/fkoh111/warp-quickstart-api-service/actions/workflows/factory-issue-labeled.yml/badge.svg)](https://github.com/fkoh111/warp-quickstart-api-service/actions/workflows/factory-issue-labeled.yml)
[![PR checks](https://github.com/fkoh111/warp-quickstart-api-service/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/fkoh111/warp-quickstart-api-service/actions/workflows/pr-checks.yml)

A self-owned GitHub Actions factory: label an issue `factory-ready` and an
OpenCode agent implements it, runs the tests, and opens a pull request for
human review, with no managed platform involved. The repository contains
the complete factory implementation (workflow, prompt template, and
OpenTofu configuration) needed to reproduce the
`01-single-repo-quickstart` pattern, plus a minimal placeholder Node.js
service for the factory to target.

> [!NOTE]
> In short: the factory is the point of this repo. The app in `app/` is
> just a stand-in target you can replace with your own project.

## Table of contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Getting started](#getting-started)
- [How it works](#how-it-works)
- [Configuration](#configuration)
- [Branch protection (managed by OpenTofu)](#branch-protection-managed-by-opentofu)
- [The target app (placeholder)](#the-target-app-placeholder)
- [Project structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

This repository implements a self-owned factory: a GitHub Actions workflow
that turns a labeled issue into a reviewed pull request using OpenCode.

The factory is intentionally minimal and auditable. It does not merge pull
requests automatically; a human reviews and merges every change.

Everything lives in one repo: the factory workflow and prompt template
(`.github/workflows/`, `factory/`), the GitHub infrastructure as code
(`tofu/`), and a trivial Node.js service (`app/`) that exists only to give
the factory something to change and CI something to run. Replace it with
your own application; see [The target app](#the-target-app-placeholder).

## Features

- Issue-triggered factory workflow (`factory-ready` label)
- OpenCode-based implementation agent with a configurable model
- **Least-privilege** workflow permissions via a dedicated GitHub App
- Automated pull requests with test and lint evidence
- Pull-request CI checks (`PR checks` workflow)
- OpenTofu-managed GitHub setup: app credentials, label, branch
  protection, workflow permissions
- Placeholder target app you can swap for your own project

## Prerequisites

- A GitHub repository with Actions enabled
- An OpenCode Zen API key (with sufficient credits)
- A GitHub App for the factory workflow (its credentials are wired up by
  OpenTofu)
- `tofu` and `gh` for applying the GitHub configuration
- Node.js 22+ and npm (only for the placeholder app and CI)

> [!TIP]
> If you're just testing locally, you can focus on `app/` and skip the
> OpenCode/OpenTofu parts.

## Getting started

1. Create a GitHub App for the factory, then apply the OpenTofu
   configuration (see
   [OpenTofu (GitHub App setup)](#opentofu-github-app-setup)). This wires
   up the app credentials, the `factory-ready` label, branch protection,
   and workflow permissions.
2. Add any model-provider secrets and the `OPENCODE_MODEL` variable (see
   [Secrets](#secrets) and [Variables](#variables)).
3. Open an issue describing the change you want.
4. Label the issue `factory-ready`.
5. The workflow implements the change, verifies it, and opens a pull
   request linked to the issue.
6. Review the pull request and merge it yourself; the factory never
   merges.

## How it works

### Trigger

An issue is labeled `factory-ready`.

### Workflow

The `Factory issue labeled` workflow:

1. Checks out the repository.
2. Installs Node.js 22 and OpenCode.
3. Runs `npm ci`, `npm test`, and `npm run lint` from `app/`.
4. Renders the implementation prompt with issue metadata.
5. Runs OpenCode with the configured model.
6. Creates a branch, commits the change, and pushes it.
7. Opens a pull request against `main`.
8. Comments on the issue with the pull request URL.

If the run fails, the workflow comments on the issue with a link to the
failed run.

### Output

- A pull request linked to the issue
- Test and lint evidence in the pull request description
- A completion or failure comment on the issue

### Safety

- The workflow uses **least-privilege** permissions.
- Branches are created under `factory/`.
- Pull requests require **human review**.
- Force pushes and branch deletions are blocked.
- The factory never merges pull requests.

## Configuration

Configure these in the repository settings.

### Secrets

| Name | Required | Purpose |
| --- | --- | --- |
| `OPENCODE_API_KEY` | Yes, for the default model | OpenCode Zen API key |
| `OPENAI_API_KEY` | Optional | Override model provider |
| `ANTHROPIC_API_KEY` | Optional | Override model provider |
| `OPENROUTER_API_KEY` | Optional | Override model provider |
| `VERCEL_API_KEY` | Optional | Override model provider |

### Variables

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| `OPENCODE_MODEL` | No | `opencode/gpt-5.4-nano` | OpenCode model ID |

### OpenTofu (GitHub App setup)

The `tofu/*.tf` files are meant to be applied with **OpenTofu** to configure
GitHub infrastructure used by the factory workflow:

- `FACTORY_APP_CLIENT_ID` (GitHub Actions repo variable)
- `FACTORY_APP_PRIVATE_KEY` (GitHub Actions repo secret)
- Optional: adding this repo to the GitHub App installation
- `factory-ready` issue label
- `main` branch protection
- Default GitHub Actions workflow permissions (so `GITHUB_TOKEN` can create PRs)

#### Prerequisites

- `tofu` installed
- A GitHub token with admin rights for the target repo (set as `GITHUB_TOKEN`)
- The GitHub App private key stored **outside** the repo (path provided to
  OpenTofu)

> [!WARNING]
> OpenTofu state will contain the private key in plaintext. Keep local
> state out of Git by using the repo's `.gitignore` (or use an encrypted
> remote backend).

#### Inputs

Configure these values via `TF_VAR_...` environment variables or `*.tfvars`
(which are ignored by git):

- `github_owner` (string)
- `repository` (string, repo name without owner)
- `factory_app_client_id` (string)
- `factory_app_private_key_path` (string, absolute or relative path)
- `factory_app_installation_id` (number, optional; default `null`)

#### Run

```bash
export GITHUB_TOKEN="$(gh auth token)"

cd tofu
tofu init
tofu plan
tofu apply
```

## Branch protection (managed by OpenTofu)

`main` is protected with:

- One required approving pull request review
- Required `test` status check from `PR checks`
- Dismissal of stale reviews
- Required conversation resolution
- No force pushes
- No branch deletions

## The target app (placeholder)

`app/` contains a trivial Node.js service whose only purpose is to give the
factory something to change and CI something to run. It is meant to be
replaced with your own application.

Any replacement must satisfy the factory's contract:

- It lives in `app/`; both workflows use that as their working directory.
- It supports `npm ci`, `npm test`, and `npm run lint`.
- Its CI produces a status check named `test`: branch protection requires
  it, and `pr-checks.yml` only runs the checks when files under `app/`
  change.

To run the placeholder locally from the repository root:

```bash
cd app
npm ci
npm test
npm run lint
```

## Project structure

```text
.
├── app/
│   ├── src/
│   │   └── index.js                      # application entry point
│   ├── test/
│   │   └── index.test.js                 # application tests
│   ├── package.json                      # Node.js project metadata and scripts
│   └── package-lock.json
├── factory/
│   └── prompts/
│       └── implement.md                  # OpenCode implementation prompt template
├── .github/
│   └── workflows/
│       ├── factory-issue-labeled.yml     # issue-triggered factory workflow
│       └── pr-checks.yml                 # pull-request CI checks
├── tofu/
│   ├── main.tf                           # OpenTofu: GitHub App credentials + repo settings
│   └── variables.tf                      # OpenTofu inputs
├── CONTRIBUTING.md                       # contribution guidelines
├── LICENSE                               # MIT license
└── README.md                             # project documentation
```

## Troubleshooting

### Free usage limit reached

Use a paid OpenCode model or add credits to the OpenCode Zen account.

### Insufficient account funds

Add credits in the OpenCode Zen billing dashboard, then re-run the
workflow.

### PR creation is blocked

Ensure GitHub Actions workflow permissions allow pull request creation:

```bash
OWNER="fkoh111"                        # your GitHub user or org
REPO="warp-quickstart-api-service"     # your repository name

gh api --method PUT "repos/${OWNER}/${REPO}/actions/permissions/workflow" \
  -f default_workflow_permissions=write \
  -F can_approve_pull_request_reviews=true
```

Or run:

```bash
cd tofu && tofu apply
```

### Required status check is waiting

The required check name must match the actual check run name. This
repository requires `test` from the `PR checks` workflow.

## Contributing

Contributions should stay small and reviewable:

1. Create a small, focused change.
2. Run `cd app && npm test` and `cd app && npm run lint`.
3. Open a pull request against `main`.
4. Request review and address feedback.

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup details and scope rules.

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.
