"""Tests for the slimmed `Verify toolchain` baseline step.

The baseline must check tool versions only; the app suite is the
scope-check step's job now.
"""

STEP = "Verify toolchain"


def test_both_jobs_share_the_same_step(scripts):
    assert scripts.get("implement_from_label", STEP) == scripts.get(
        "implement_from_comment", STEP
    )


def test_checks_versions_without_npm(sandbox, scripts):
    script = scripts.get("implement_from_label", STEP)

    result = sandbox.run(script)

    assert result.returncode == 0, result.stderr
    log = sandbox.shim_log()
    assert "node --version" in log
    assert "opencode --version" in log
    assert not any(line.startswith("npm") for line in log)


def test_fails_when_a_tool_is_missing(sandbox, scripts):
    script = scripts.get("implement_from_label", STEP)

    result = sandbox.run(script, env_extra={"SHIM_FAIL_OPENCODE": "1"})

    assert result.returncode != 0
