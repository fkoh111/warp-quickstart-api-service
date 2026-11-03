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
  --input .github/branch-protection.json

echo "Bootstrap complete for $REPO"
echo "Label: $LABEL"
echo "Branch protection applied to main"
