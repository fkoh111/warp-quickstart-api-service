#!/usr/bin/env bash
set -euo pipefail

REPO="${1:?Usage: $0 owner/repo}"
LABEL="factory-ready"
COLOR="0e8a16"
DESCRIPTION="Trigger the self-owned factory workflow"

if gh label list --repo "$REPO" --json name --jq '.[].name' | grep -qx "$LABEL"; then
  gh label edit "$LABEL" \
    --repo "$REPO" \
    --color "$COLOR" \
    --description "$DESCRIPTION"
else
  gh label create "$LABEL" \
    --repo "$REPO" \
    --color "$COLOR" \
    --description "$DESCRIPTION"
fi

gh api \
  --method PUT \
  "repos/$REPO/branches/main/protection" \
  --input factory/branch-protection.json

# Allow the default GITHUB_TOKEN to create pull requests. This is required
# for the factory workflow to open PRs without a separate app token.
gh api \
  --method PUT \
  "repos/$REPO/actions/permissions/workflow" \
  -f default_workflow_permissions=write \
  -F can_approve_pull_request_reviews=true

echo "Bootstrap complete for $REPO"
echo "Label: $LABEL"
echo "Branch protection applied to main"
echo "GitHub Actions workflow permissions updated"
