# Warp Quickstart API Service

[![Factory issue labeled](https://github.com/fkoh111/warp-quickstart-api-service/actions/workflows/factory-issue-labeled.yml/badge.svg)](https://github.com/fkoh111/warp-quickstart-api-service/actions/workflows/factory-issue-labeled.yml)
[![PR checks](https://github.com/fkoh111/warp-quickstart-api-service/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/fkoh111/warp-quickstart-api-service/actions/workflows/pr-checks.yml)

A minimal Node.js service used as the target repository for a self-owned
GitHub Actions factory workflow. The repository also contains the factory
definition, automation, runner, prompts, and GitHub bootstrap scripts needed
to reproduce the `01-single-repo-quickstart` pattern without a managed
platform.

## Overview

This project has two parts:

1. **Application code**: a small Node.js service with tests and linting.
2. **Self-owned factory**: a GitHub Actions workflow that turns a labeled
   issue into a pull request using OpenCode.

The factory is intentionally minimal and auditable. It does not merge pull
requests automatically; a human reviews and merges every change.

## Features

- Minimal Node.js service with `node:test` tests
- GitHub Actions workflow triggered by `factory-ready` issues
- OpenCode-based implementation agent
- Least-privilege workflow permissions
- Pull-request CI checks
- Branch protection and label bootstrap script
- Docker runner image for local parity

## Prerequisites

- Node.js 22 or newer
- npm
- Docker, for optional local runner validation
- A GitHub repository with Actions enabled
- An OpenCode Zen API key with sufficient credits

## Getting started

Install dependencies:

```bash
cd app && npm install
```

Run tests:

```bash
cd app && npm test
```

Run lint:

```bash
cd app && npm run lint
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
│   ├── prompts/
│   │   └── implement.md                # OpenCode implementation prompt template
│   ├── docker/
│   │   └── runner.Dockerfile           # optional local runner image
│   ├── scripts/
│   │   └── bootstrap-github.sh         # one-time/manual GitHub settings setup
│   └── branch-protection.json         # desired branch protection settings
├── .github/
│   └── workflows/
│       ├── factory-issue-labeled.yml  # issue-triggered factory workflow
│       └── pr-checks.yml              # pull-request CI checks
├── LICENSE                           # MIT license
└── README.md                         # project documentation
```

## Self-owned factory

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

- The workflow uses least-privilege permissions.
- Branches are created under `factory/`.
- Pull requests require human review.
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

## Bootstrap GitHub settings

Create the `factory-ready` label and apply branch protection:

```bash
./factory/scripts/bootstrap-github.sh fkoh111/warp-quickstart-api-service
```

This script is a one-time/manual setup tool. The factory workflow does not invoke it.

The script also configures GitHub Actions workflow permissions so the
default `GITHUB_TOKEN` can create pull requests.

## Branch protection

`main` is protected with:

- One required approving pull request review
- Required `test` status check from `PR checks`
- Dismissal of stale reviews
- Required conversation resolution
- No force pushes
- No branch deletions

## Docker runner

Build the optional local runner image:

```bash
docker build -f factory/docker/runner.Dockerfile -t factory-runner .
```

Run the toolchain and tests in the image:

```bash
docker run --rm -v "$PWD:/work" -w /work/app factory-runner \
  sh -c 'npm ci && npm test && npm run lint'
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
gh api --method PUT repos/fkoh111/warp-quickstart-api-service/actions/permissions/workflow \
  -f default_workflow_permissions=write \
  -F can_approve_pull_request_reviews=true
```

Or run:

```bash
./factory/scripts/bootstrap-github.sh fkoh111/warp-quickstart-api-service
```

### Required status check is waiting

The required check name must match the actual check run name. This
repository requires `test` from the `PR checks` workflow.

## Contributing

1. Create a small, focused change.
2. Run `cd app && npm test` and `cd app && npm run lint`.
3. Open a pull request against `main`.
4. Request review and address feedback.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
```<|end|><|start|>write to=assistant<|channel|>analysis<|message|>Created file successfully: /home/fkoh111/Projects/warp-quickstart-api-service/README.md
