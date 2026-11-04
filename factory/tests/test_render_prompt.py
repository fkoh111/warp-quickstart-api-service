"""Tests for the `Render agent prompt` step.

Runs the real python renderer against the real prompt template and
checks that every placeholder is substituted.
"""

import re

import pytest

from conftest import RENDERED_PROMPT_PATH

STEP = "Render agent prompt"
PLACEHOLDER_KEYS = (
    "REPOSITORY",
    "ISSUE_NUMBER",
    "ISSUE_TITLE",
    "ISSUE_BODY",
    "DEFAULT_BRANCH",
    "EXISTING_BRANCH",
    "EXISTING_PR_URL",
    "EXISTING_PR_NUMBER",
)


@pytest.fixture(autouse=True)
def cleanup_rendered():
    RENDERED_PROMPT_PATH.unlink(missing_ok=True)
    yield
    RENDERED_PROMPT_PATH.unlink(missing_ok=True)


def test_all_placeholders_are_substituted(sandbox, factory_cwd, scripts):
    script = scripts.get("implement_from_label", STEP)

    result = sandbox.run(script, cwd=factory_cwd)

    assert result.returncode == 0, result.stderr
    rendered = RENDERED_PROMPT_PATH.read_text()
    for key in PLACEHOLDER_KEYS:
        assert f"${key}" not in rendered
    assert "Repository: test-owner/test-repo" in rendered
    assert "Issue number: 42" in rendered
    assert "factory/issue-42-" in rendered
    assert "Closes #42" in rendered


def test_comment_body_is_appended_to_issue_body(
    sandbox, factory_cwd, scripts
):
    script = scripts.get("implement_from_label", STEP)

    result = sandbox.run(
        script,
        cwd=factory_cwd,
        env_extra={"COMMENT_BODY": "please also fix the docs"},
    )

    assert result.returncode == 0, result.stderr
    rendered = RENDERED_PROMPT_PATH.read_text()
    assert "Latest comment:" in rendered
    assert "please also fix the docs" in rendered


def test_issue_body_multiline_survives_rendering(sandbox, factory_cwd, scripts):
    script = scripts.get("implement_from_label", STEP)
    body = "First line\n\nSecond paragraph with `code`."

    result = sandbox.run(script, cwd=factory_cwd, env_extra={"ISSUE_BODY": body})

    assert result.returncode == 0, result.stderr
    rendered = RENDERED_PROMPT_PATH.read_text()
    assert body in rendered
    # The template structure must remain intact after substitution.
    assert re.search(r"^Verification:$", rendered, re.MULTILINE)
    assert re.search(r"^Constraints:$", rendered, re.MULTILINE)
