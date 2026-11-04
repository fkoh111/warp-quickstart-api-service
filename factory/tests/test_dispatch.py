"""Tests for the workflow_dispatch `Resolve issue metadata` step.

On dispatch events the issue title/body are not in the event payload, so
the step fetches them via `gh api` and writes multiline-safe
GITHUB_OUTPUT entries consumed by the `Render agent prompt` step.
"""

JOB = "implement_from_label"
STEP = "Resolve issue metadata"


def test_single_line_issue(sandbox, scripts):
    script = scripts.get(JOB, STEP)
    sandbox.set_gh_response(
        {"title": "Add health endpoint", "body": "Please add /health"}
    )

    result = sandbox.run(script)

    assert result.returncode == 0, result.stderr
    outputs = sandbox.outputs()
    assert outputs["title"] == "Add health endpoint"
    assert outputs["body"] == "Please add /health"


def test_multiline_body_survives_output_parsing(sandbox, scripts):
    script = scripts.get(JOB, STEP)
    body = "First line\n\nSecond paragraph with a list:\n- one\n- two"
    sandbox.set_gh_response({"title": "Multi", "body": body})

    result = sandbox.run(script)

    assert result.returncode == 0, result.stderr
    assert sandbox.outputs()["body"] == body


def test_null_body_becomes_empty_string(sandbox, scripts):
    script = scripts.get(JOB, STEP)
    sandbox.set_gh_response({"title": "No body", "body": None})

    result = sandbox.run(script)

    assert result.returncode == 0, result.stderr
    outputs = sandbox.outputs()
    assert outputs["title"] == "No body"
    assert outputs["body"] == ""


def test_queries_the_configured_repository_and_issue(sandbox, scripts):
    script = scripts.get(JOB, STEP)
    sandbox.set_gh_response({"title": "t", "body": "b"})

    result = sandbox.run(script)

    assert result.returncode == 0, result.stderr
    assert (
        "gh api repos/test-owner/test-repo/issues/42" in sandbox.shim_log()
    )


def test_fails_when_the_api_call_fails(sandbox, scripts):
    script = scripts.get(JOB, STEP)

    result = sandbox.run(script, env_extra={"SHIM_FAIL_GH": "1"})

    assert result.returncode != 0
