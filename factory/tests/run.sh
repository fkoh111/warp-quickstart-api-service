#!/usr/bin/env bash
# One-command runner for the factory test suite.
#
# - Creates a Python venv (factory/tests/.venv) on first run
# - Runs actionlint static analysis (via Docker, or a local binary)
# - Runs the pytest unit tests against the real workflow scripts
set -euo pipefail

cd "$(dirname "$0")"
TESTS_DIR="$PWD"
REPO_ROOT="$(cd ../.. && pwd)"

if [[ ! -d .venv ]]; then
  echo "==> Creating Python venv"
  python3 -m venv .venv
fi

echo "==> Installing test dependencies"
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -r "${REPO_ROOT}/requirements.txt"

echo "==> Static analysis (actionlint)"
# The action metadata bundled with actionlint predates the client-id input
# of actions/create-github-app-token@v3 (upstream deprecated app-id in
# favor of client-id), so those two findings are false positives.
ACTIONLINT_IGNORES=(
  -ignore "input \"client-id\" is not defined in action \"actions/create-github-app-token"
  -ignore "missing input \"app-id\" which is required by action \"actions/create-github-app-token"
)
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  docker run --rm -v "${REPO_ROOT}:/repo" -w /repo rhysd/actionlint -color \
    "${ACTIONLINT_IGNORES[@]}"
elif command -v actionlint >/dev/null 2>&1; then
  (cd "${REPO_ROOT}" && actionlint -color "${ACTIONLINT_IGNORES[@]}")
else
  echo "WARN: neither Docker nor actionlint found; skipping static analysis" >&2
fi

echo "==> Unit tests (pytest)"
cd "${TESTS_DIR}"
./.venv/bin/pytest -q
