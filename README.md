# Warp Quickstart API Service

Minimal Node.js service used as the target repository for a self-owned
factory workflow.

## Local development

1. Install Node.js 22 (or newer)
2. Install dependencies: `npm install`
3. Run `npm test` and `npm run lint` before opening a pull request

## Self-owned factory

This repository contains a GitHub Actions workflow that implements the
`01-single-repo-quickstart` pattern without a managed platform:

- Trigger: an issue is labeled `factory-ready`
- Runner: GitHub-hosted Ubuntu with Node.js 22 and OpenCode
- Agent: OpenCode, configured by the `OPENCODE_MODEL` repository variable
- Output: a pull request linked to the issue, plus a completion/failure
  comment

Required GitHub configuration:

- Secret: `OPENCODE_API_KEY` for the default `opencode/beam-free` model,
  or `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, or
  `VERCEL_API_KEY` for an override
- Variable: `OPENCODE_MODEL` (optional, defaults to
  `opencode/gpt-5.4-nano`)
- Branch protection and the `factory-ready` label can be created with:

```bash
./scripts/bootstrap-github.sh fkoh111/warp-quickstart-api-service
```

The workflow uses least-privilege permissions and does not merge pull
requests automatically.
