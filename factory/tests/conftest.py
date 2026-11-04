"""Shared fixtures for the factory workflow test suite.

The tests execute the *actual* ``run:`` blocks extracted from
``.github/workflows/factory-issue-labeled.yml`` inside a sandbox that
mimics a GitHub Actions runner:

- throwaway git repositories (a bare ``origin`` plus clones over
  ``file://``), so no network is needed
- PATH shims for external commands (``npm``, ``gh``, ``node``,
  ``opencode``) that record every invocation
- a real ``GITHUB_OUTPUT`` file, parsed back into a dict for assertions
"""

import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest
import yaml

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "factory-issue-labeled.yml"

# The renderer step hardcodes its output path; tests read and remove it.
RENDERED_PROMPT_PATH = Path("/tmp/factory-prompt.md")

# Deterministic values substituted into ${{ ... }} expressions that appear
# inside run: blocks (env-value expressions never reach the scripts).
EXPRESSION_VALUES = {
    "github.server_url": "https://github.com",
    "github.repository": "test-owner/test-repo",
    "github.run_id": "987654321",
}

SHIM_NAMES = ("npm", "gh", "node", "opencode")

SHIM_TEMPLATE = """#!/usr/bin/env bash
name="$(basename "$0")"
printf '%s %s\\n' "$name" "$*" >> "$SHIM_LOG"
if [[ "$name" == "gh" && "${1:-}" == "api" && -n "${GH_RESPONSE_FILE:-}" ]]; then
  cat "$GH_RESPONSE_FILE"
  exit 0
fi
if [[ "$name" == "gh" && "${1:-}" == "issue" && "${2:-}" == "view" && -n "${GH_RESPONSE_FILE:-}" ]]; then
  # Apply --jq filter if present (jq is available on the runner).
  jq_filter=""
  args=("$@")
  for ((i=0; i<$#; i++)); do
    if [[ "${args[$i]}" == "--jq" ]]; then
      jq_filter="${args[$((i+1))]}"
      break
    fi
  done
  if [[ -n "$jq_filter" ]]; then
    jq -r "$jq_filter" < "$GH_RESPONSE_FILE"
  else
    cat "$GH_RESPONSE_FILE"
  fi
  exit 0
fi
if [[ "$name" == "gh" && "${1:-}" == "issue" && "${2:-}" == "edit" ]]; then
  exit 0
fi
fail_var="SHIM_FAIL_$(printf '%s' "$name" | tr '[:lower:]' '[:upper:]')"
if [[ -n "${!fail_var:-}" ]]; then
  exit 1
fi
case "$name" in
  node) printf 'v22.0.0-shim\\n' ;;
  opencode) printf '1.0.0-shim\\n' ;;
esac
exit 0
"""

BASE_TREE = {
    "README.md": "# test repo\n",
    "app/package.json": '{"name": "placeholder", "scripts": {"test": "true"}}\n',
    "app/src/index.js": "console.log('hello');\n",
    ".github/workflows/pr-checks.yml": "name: PR checks\n",
    "tofu/main.tf": "# tofu\n",
}


def substitute_expressions(script):
    """Replace ``${{ ... }}`` expressions with deterministic test values."""

    def repl(match):
        expr = match.group(1).strip()
        return EXPRESSION_VALUES.get(expr, "placeholder")

    return re.sub(r"\$\{\{([^}]*)\}\}", repl, script)


class WorkflowScripts:
    """Extracts real ``run:`` blocks from the factory workflow."""

    def __init__(self):
        with open(WORKFLOW_PATH) as handle:
            self._doc = yaml.safe_load(handle)

    def get(self, job, step_name):
        for step in self._doc["jobs"][job]["steps"]:
            if step.get("name") == step_name:
                if "run" not in step:
                    raise KeyError(
                        f"step {step_name!r} in job {job!r} has no run block"
                    )
                return substitute_expressions(step["run"])
        raise KeyError(f"no step {step_name!r} in job {job!r}")

    def step_names(self, job):
        return [step.get("name") for step in self._doc["jobs"][job]["steps"]]


@pytest.fixture(scope="session")
def scripts():
    return WorkflowScripts()


class Sandbox:
    """A runner-like environment: git repos, shims, env, GITHUB_OUTPUT."""

    def __init__(self, tmp_path):
        self.root = tmp_path
        self._build_shims()
        self._build_repos()

        self.output_file = tmp_path / "github_output"
        self.output_file.touch()
        self.shim_log_file = tmp_path / "shim.log"
        self.shim_log_file.touch()
        self.gh_response_file = tmp_path / "gh_response.json"

        self.env = {
            "PATH": f"{self.shim_dir}:{os.environ['PATH']}",
            "HOME": str(self.home),
            "GITHUB_OUTPUT": str(self.output_file),
            "SHIM_LOG": str(self.shim_log_file),
            "REPOSITORY": "test-owner/test-repo",
            "ISSUE_NUMBER": "42",
            "ISSUE_TITLE": "Test issue",
            "ISSUE_BODY": "Please implement the thing.",
            "COMMENT_BODY": "",
            "DEFAULT_BRANCH": "main",
            "EXISTING_BRANCH": "",
            "EXISTING_PR_URL": "",
            "EXISTING_PR_NUMBER": "",
            "GH_TOKEN": "fake-token",
            "RUN_URL": "https://github.com/test-owner/test-repo/actions/runs/987654321",
        }

    # -- setup helpers ----------------------------------------------------

    def _build_shims(self):
        self.shim_dir = self.root / "shims"
        self.shim_dir.mkdir()
        for name in SHIM_NAMES:
            shim = self.shim_dir / name
            shim.write_text(SHIM_TEMPLATE)
            shim.chmod(
                shim.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            )
        self.home = self.root / "home"
        self.home.mkdir()

    def _cmd(self, args, cwd):
        result = subprocess.run(
            args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": str(self.home)},
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"{' '.join(args)} failed ({result.returncode}): {result.stderr}"
            )
        return result.stdout

    def _configure_identity(self, repo):
        self._cmd(["git", "config", "user.name", "Factory Test"], cwd=repo)
        self._cmd(
            ["git", "config", "user.email", "factory-test@example.invalid"],
            cwd=repo,
        )

    def _write_tree(self, repo, files):
        for path, content in files.items():
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)

    def _build_repos(self):
        self.origin = self.root / "origin.git"
        self._cmd(
            ["git", "init", "--bare", "-b", "main", str(self.origin)],
            cwd=self.root,
        )

        self.seed = self.root / "seed"
        self._cmd(["git", "clone", str(self.origin), "seed"], cwd=self.root)
        self._configure_identity(self.seed)
        self._write_tree(self.seed, BASE_TREE)
        self._cmd(["git", "add", "-A"], cwd=self.seed)
        self._cmd(["git", "commit", "-m", "base tree"], cwd=self.seed)
        self._cmd(["git", "push", "-u", "origin", "main"], cwd=self.seed)

        self.work = self.root / "work"
        self._cmd(["git", "clone", str(self.origin), "work"], cwd=self.root)
        self._configure_identity(self.work)

    # -- test helpers ------------------------------------------------------

    def create_branch(self, name, files, base="main"):
        """Push a branch with the given file changes to origin."""
        self._cmd(["git", "fetch", "origin"], cwd=self.seed)
        self._cmd(
            ["git", "checkout", "-B", name, f"origin/{base}"], cwd=self.seed
        )
        self._write_tree(self.seed, files)
        self._cmd(["git", "add", "-A"], cwd=self.seed)
        self._cmd(["git", "commit", "-m", f"change for {name}"], cwd=self.seed)
        self._cmd(["git", "push", "origin", name], cwd=self.seed)

    def set_gh_response(self, payload):
        """Make the gh shim answer `gh api` calls with this JSON payload."""
        self.gh_response_file.write_text(json.dumps(payload))
        self.env["GH_RESPONSE_FILE"] = str(self.gh_response_file)

    def run(self, script, env_extra=None, cwd=None):
        env = {**self.env, **(env_extra or {})}
        return subprocess.run(
            ["bash", "-c", script],
            cwd=str(cwd or self.work),
            capture_output=True,
            text=True,
            env=env,
        )

    def shim_log(self):
        return self.shim_log_file.read_text().splitlines()

    def shim_log_text(self):
        return self.shim_log_file.read_text()

    def outputs(self):
        """Parse GITHUB_OUTPUT, supporting key=value and heredoc forms."""
        result = {}
        lines = self.output_file.read_text().splitlines()
        index = 0
        while index < len(lines):
            line = lines[index]
            if "<<" in line:
                key, delimiter = line.split("<<", 1)
                collected = []
                index += 1
                while index < len(lines) and lines[index] != delimiter:
                    collected.append(lines[index])
                    index += 1
                result[key] = "\n".join(collected)
            elif "=" in line:
                key, _, value = line.partition("=")
                result[key] = value
            index += 1
        return result


@pytest.fixture()
def sandbox(tmp_path):
    return Sandbox(tmp_path)


@pytest.fixture()
def factory_cwd(sandbox):
    """A directory shaped like `factory/` holding the real prompt template."""
    target = sandbox.root / "factory-run"
    (target / "prompts").mkdir(parents=True)
    shutil.copy(
        REPO_ROOT / "factory" / "prompts" / "implement.md",
        target / "prompts" / "implement.md",
    )
    return target
