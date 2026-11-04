"""Tests for the styled issue comments posted by both jobs."""

SUCCESS_STEP = "Comment on issue on success"
FAILURE_STEP = "Comment on issue on failure"

PR_URL = "https://github.com/test-owner/test-repo/pull/7"
EVIDENCE = "app/ changed; npm ci, npm test, and npm run lint passed"


def test_both_jobs_share_comment_steps(scripts):
    for job in ("implement_from_label", "implement_from_comment"):
        assert scripts.get(job, SUCCESS_STEP)
        assert scripts.get(job, FAILURE_STEP)


def test_success_comment_is_styled_markdown(sandbox, scripts):
    script = scripts.get("implement_from_label", SUCCESS_STEP)

    result = sandbox.run(
        script, env_extra={"PR_URL": PR_URL, "EVIDENCE": EVIDENCE}
    )

    assert result.returncode == 0, result.stderr
    body = sandbox.shim_log_text()
    assert "gh issue comment 42 --repo test-owner/test-repo --body" in body
    assert "✅ **Factory run succeeded**" in body
    assert f"Pull request: {PR_URL}" in body
    assert "<details>" in body and "<summary>Evidence</summary>" in body
    assert EVIDENCE in body


def test_success_comment_falls_back_without_evidence(sandbox, scripts):
    script = scripts.get("implement_from_label", SUCCESS_STEP)

    result = sandbox.run(
        script, env_extra={"PR_URL": PR_URL, "EVIDENCE": ""}
    )

    assert result.returncode == 0, result.stderr
    assert "no evidence reported" in sandbox.shim_log_text()


def test_failure_comment_is_enriched(sandbox, scripts):
    script = scripts.get("implement_from_label", FAILURE_STEP)

    result = sandbox.run(
        script,
        env_extra={
            "RUN_URL": "https://github.com/test-owner/test-repo/actions/runs/987654321",
            "ERROR_TAIL": "Error: patch verification failed\nFailed to read file",
            "TRIPPED": "false",
        },
    )

    assert result.returncode == 0, result.stderr
    body = sandbox.shim_log_text()
    assert "❌ **Factory run failed**" in body
    assert "**Error summary (last 20 lines):**" in body
    assert "Error: patch verification failed" in body
    assert "[workflow run](https://github.com/test-owner/test-repo/actions/runs/987654321)" in body


def test_failure_comment_escalates_after_circuit_breaker(sandbox, scripts):
    script = scripts.get("implement_from_label", FAILURE_STEP)

    result = sandbox.run(
        script,
        env_extra={
            "RUN_URL": "https://github.com/test-owner/test-repo/actions/runs/987654321",
            "ERROR_TAIL": "Error: patch verification failed",
            "TRIPPED": "true",
        },
    )

    assert result.returncode == 0, result.stderr
    body = sandbox.shim_log_text()
    assert "❌ **Factory run failed (escalated)**" in body
    assert "Manual intervention required" in body
    assert "factory-failed" in body  # gh issue edit --add-label factory-failed
