import os
import sys
import subprocess

def test_cli_no_args_shows_usage():
    result = subprocess.run(
        [sys.executable, "hired_score.py"],
        capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower()

def test_cli_score_requires_api_key():
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    result = subprocess.run(
        [sys.executable, "hired_score.py", "score"],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=env,
    )
    output = result.stdout + result.stderr
    assert "ANTHROPIC_API_KEY" in output
