"""Tests for the `Verify repository layout` pre-flight step.

The step runs from factory/ and verifies that the expected repo-root
paths exist via ../ prefixes. It must fail fast with a clear message
if the layout is wrong.
"""

STEP = "Verify repository layout"


def test_passes_with_correct_layout(sandbox, scripts):
    script = scripts.get("implement_from_label", STEP)

    # The step runs from factory/, so create that subdirectory
    factory_dir = sandbox.work / "factory"
    factory_dir.mkdir(exist_ok=True)

    result = sandbox.run(script, cwd=factory_dir)

    assert result.returncode == 0, result.stderr
    assert "Repository layout OK" in result.stdout


def test_fails_when_workflows_dir_missing(sandbox, scripts):
    script = scripts.get("implement_from_label", STEP)

    import shutil
    factory_dir = sandbox.work / "factory"
    factory_dir.mkdir(exist_ok=True)
    workflows = sandbox.work / ".github" / "workflows"
    if workflows.exists():
        shutil.rmtree(workflows)

    result = sandbox.run(script, cwd=factory_dir)

    assert result.returncode != 0
    assert "Expected path does not exist" in result.stderr


def test_fails_when_app_dir_missing(sandbox, scripts):
    script = scripts.get("implement_from_label", STEP)

    import shutil
    factory_dir = sandbox.work / "factory"
    factory_dir.mkdir(exist_ok=True)
    app_dir = sandbox.work / "app"
    if app_dir.exists():
        shutil.rmtree(app_dir)

    result = sandbox.run(script, cwd=factory_dir)

    assert result.returncode != 0
    assert "Expected path does not exist" in result.stderr


def test_step_exists_in_both_jobs(scripts):
    assert scripts.get("implement_from_label", STEP)
    assert scripts.get("implement_from_comment", STEP)
    assert scripts.get("implement_from_comment", STEP)
