# Warp Quickstart API Service

Minimal Node.js service used as the target repository for a self-owned
factory workflow.

## Local development

1. Install dependencies: `npm install`
2. Run tests: `npm test`
3. Run lint: `npm run lint`

## Self-owned factory

This repository contains a GitHub Actions workflow that implements the
`01-single-repo-quickstart` pattern without a managed platform:

- Trigger: an issue is labeled `factory-ready`
- Runner: GitHub-hosted Ubuntu with Node.js 22 and OpenCode
- Agent: OpenCode, configured by the `OPENCODE_MODEL` repository variable
- Output: a pull request linked to the issue, plus a completion/failure
  comment

Required GitHub configuration:

- Secret: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENROUTER_API_KEY`,
  depending on the selected model
- Variable: `OPENCODE_MODEL`, for example `openai/gpt-5`
- Branch protection and the `factory-ready` label can be created with:

```bash
./scripts/bootstrap-github.sh fkoh111/warp-quickstart-api-service
```

The workflow uses least-privilege permissions and does not merge pull
requests automatically.
