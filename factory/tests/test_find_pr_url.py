"""Tests for the `Find PR URL for the issue` step.

Verifies the jq filter fix (piping through jq instead of --arg on gh api)
and the EXISTING_PR_URL passthrough.
"""

STEP = "Find PR URL for the issue"


def test_existing_pr_url_passthrough(sandbox, scripts):
    script = scripts.get("implement_from_label", STEP)

    result = sandbox.run(
        script,
        env_extra={"EXISTING_PR_URL": "https://github.com/test-owner/test-repo/pull/99"},
    )

    assert result.returncode == 0, result.stderr
    assert sandbox.outputs()["url"] == "https://github.com/test-owner/test-repo/pull/99"
    # Should NOT have called gh api
    assert not any("gh api" in line for line in sandbox.shim_log())


def test_finds_pr_by_branch_prefix(sandbox, scripts):
    script = scripts.get("implement_from_label", STEP)

    sandbox.set_gh_response([
        {"head": {"ref": "main"}, "updated_at": "2026-01-01T00:00:00Z", "html_url": "https://github.com/test-owner/test-repo/pull/1"},
        {"head": {"ref": "factory/issue-42-foo"}, "updated_at": "2026-01-02T00:00:00Z", "html_url": "https://github.com/test-owner/test-repo/pull/2"},
        {"head": {"ref": "factory/issue-42-bar"}, "updated_at": "2026-01-03T00:00:00Z", "html_url": "https://github.com/test-owner/test-repo/pull/3"},
    ])

    result = sandbox.run(script, env_extra={"ISSUE_NUMBER": "42"})

    assert result.returncode == 0, result.stderr
    # Should pick the most recently updated PR (issue-42-bar)
    assert sandbox.outputs()["url"] == "https://github.com/test-owner/test-repo/pull/3"


def test_fails_when_no_pr_found(sandbox, scripts):
    script = scripts.get("implement_from_label", STEP)

    sandbox.set_gh_response([
        {"head": {"ref": "main"}, "updated_at": "2026-01-01T00:00:00Z", "html_url": "https://github.com/test-owner/test-repo/pull/1"},
    ])

    result = sandbox.run(script, env_extra={"ISSUE_NUMBER": "99"})

    assert result.returncode != 0
    assert "No PR found" in result.stderr


def test_fails_when_gh_api_fails(sandbox, scripts):
    script = scripts.get("implement_from_label", STEP)

    result = sandbox.run(script, env_extra={"SHIM_FAIL_GH": "1", "ISSUE_NUMBER": "42"})

    assert result.returncode != 0


def test_step_exists_in_both_jobs(scripts):
    assert scripts.get("implement_from_label", STEP)
    assert scripts.get("implement_from_comment", STEP)
