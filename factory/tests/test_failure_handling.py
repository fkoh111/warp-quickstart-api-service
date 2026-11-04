"""Tests for the failure-handling steps added in Phases 2 and 4.

- "Capture failure context": reads the tail of the agent log and writes
  it to GITHUB_OUTPUT.
- "Check circuit breaker": counts factory-attempt-* labels and decides
  whether to escalate.
"""

from pathlib import Path

CAPTURE_STEP = "Capture failure context"
BREAKER_STEP = "Check circuit breaker"


def test_capture_failure_context_reads_log_tail(sandbox, scripts):
    script = scripts.get("implement_from_label", CAPTURE_STEP)

    # Create a log file with more than 20 lines in RUNNER_TEMP
    log_dir = Path(sandbox.env["RUNNER_TEMP"]) / "factory-runs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "issue-42.log"
    lines = [f"line {i}" for i in range(1, 31)]
    log_path.write_text("\n".join(lines) + "\n")

    result = sandbox.run(script)

    assert result.returncode == 0, result.stderr
    outputs = sandbox.outputs()
    assert "line 30" in outputs["tail"]
    assert "line 11" in outputs["tail"]
    assert "line 10" not in outputs["tail"]


def test_capture_failure_context_handles_missing_log(sandbox, scripts):
    script = scripts.get("implement_from_label", CAPTURE_STEP)

    result = sandbox.run(script)

    assert result.returncode == 0, result.stderr
    outputs = sandbox.outputs()
    assert outputs["tail"] == "No agent log available."


def test_circuit_breaker_not_tripped_on_first_failure(sandbox, scripts):
    script = scripts.get("implement_from_label", BREAKER_STEP)

    # gh shim returns 0 attempt labels
    sandbox.set_gh_response({"labels": []})

    result = sandbox.run(script)

    assert result.returncode == 0, result.stderr
    assert sandbox.outputs()["tripped"] == "false"
    # Should have added factory-attempt-1 label
    assert "factory-attempt-1" in sandbox.shim_log_text()


def test_circuit_breaker_tripped_after_two_failures(sandbox, scripts):
    script = scripts.get("implement_from_label", BREAKER_STEP)

    # gh shim returns 2 attempt labels
    sandbox.set_gh_response(
        {"labels": [{"name": "factory-attempt-1"}, {"name": "factory-attempt-2"}]}
    )

    result = sandbox.run(script)

    assert result.returncode == 0, result.stderr
    assert sandbox.outputs()["tripped"] == "true"
    # factory-failed label is added in the failure comment step, not here


def test_circuit_breaker_one_attempt_label(sandbox, scripts):
    script = scripts.get("implement_from_label", BREAKER_STEP)

    sandbox.set_gh_response(
        {"labels": [{"name": "factory-attempt-1"}]}
    )

    result = sandbox.run(script)

    assert result.returncode == 0, result.stderr
    assert sandbox.outputs()["tripped"] == "false"
    assert "factory-attempt-2" in sandbox.shim_log_text()
