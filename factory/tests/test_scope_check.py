"""Tests for the `Verify change scope` step in both jobs.

The step must run the app suite only when the pushed branch changes
files under app/, honor EXISTING_BRANCH, and emit honest evidence to
GITHUB_OUTPUT.
"""

import pytest

JOB = "implement_from_label"
STEP = "Verify change scope"

EVIDENCE_APP = "app/ changed; npm ci, npm test, and npm run lint passed"
EVIDENCE_SKIP = "no app/ changes; app suite skipped"


@pytest.fixture()
def script(scripts):
    return scripts.get(JOB, STEP)


def test_both_jobs_share_the_same_step(scripts):
    assert scripts.get(JOB, STEP) == scripts.get("implement_from_comment", STEP)


def test_app_change_runs_the_suite(sandbox, script):
    sandbox.create_branch(
        "factory/issue-42-add-endpoint",
        {"app/src/index.js": "console.log('changed');\n"},
    )

    result = sandbox.run(script)

    assert result.returncode == 0, result.stderr
    log = sandbox.shim_log()
    assert "npm ci" in log
    assert "npm test" in log
    assert "npm run lint" in log
    assert sandbox.outputs()["evidence"] == EVIDENCE_APP


def test_factory_only_change_skips_the_suite(sandbox, script):
    sandbox.create_branch(
        "factory/issue-42-tweak-prompt",
        {"factory/prompts/implement.md": "tweaked\n"},
    )

    result = sandbox.run(script)

    assert result.returncode == 0, result.stderr
    assert not any(line.startswith("npm") for line in sandbox.shim_log())
    assert sandbox.outputs()["evidence"] == EVIDENCE_SKIP


def test_mixed_change_counts_as_app_change(sandbox, script):
    sandbox.create_branch(
        "factory/issue-42-mixed",
        {
            "app/src/index.js": "console.log('mixed');\n",
            "README.md": "# touched too\n",
        },
    )

    result = sandbox.run(script)

    assert result.returncode == 0, result.stderr
    assert "npm test" in sandbox.shim_log()
    assert sandbox.outputs()["evidence"] == EVIDENCE_APP


def test_existing_branch_is_honored(sandbox, script):
    sandbox.create_branch(
        "factory/issue-42-app-change", {"app/src/index.js": "x\n"}
    )
    sandbox.create_branch("factory/issue-42-docs", {"README.md": "docs\n"})

    result = sandbox.run(
        script, env_extra={"EXISTING_BRANCH": "factory/issue-42-docs"}
    )

    assert result.returncode == 0, result.stderr
    assert not any(line.startswith("npm") for line in sandbox.shim_log())
    assert sandbox.outputs()["evidence"] == EVIDENCE_SKIP


def test_branch_resolution_picks_sorted_last(sandbox, script):
    # No EXISTING_BRANCH: the step resolves factory/issue-<N>-* branches
    # and picks the sorted-last one (zzz: factory-only).
    sandbox.create_branch("factory/issue-42-aaa", {"app/src/index.js": "a\n"})
    sandbox.create_branch("factory/issue-42-zzz", {"README.md": "z\n"})

    result = sandbox.run(script)

    assert result.returncode == 0, result.stderr
    assert sandbox.outputs()["evidence"] == EVIDENCE_SKIP


def test_app_suite_failure_fails_the_step(sandbox, script):
    sandbox.create_branch(
        "factory/issue-42-broken", {"app/src/index.js": "broken\n"}
    )

    result = sandbox.run(script, env_extra={"SHIM_FAIL_NPM": "1"})

    assert result.returncode != 0
    assert "evidence" not in sandbox.outputs()
