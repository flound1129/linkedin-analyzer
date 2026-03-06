"""Integration tests — require ANTHROPIC_API_KEY to be set."""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)

from profile_loader import load_profile, profile_to_text
from scoring_prompt import build_scoring_system_prompt, build_scoring_user_message
from audit_prompt import build_audit_system_prompt, build_audit_user_message
import anthropic
import json


def call_claude(system_prompt, user_message):
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
    return json.loads(text)


def test_score_returns_valid_structure():
    profile = load_profile()
    profile_text = profile_to_text(profile)
    result = call_claude(
        build_scoring_system_prompt(),
        build_scoring_user_message(profile_text),
    )
    assert result["grade"] in ("A", "B", "C", "D")
    assert 0 <= result["total_score"] <= 100
    assert len(result["factors"]) == 6
    assert all("score" in f and "max_score" in f for f in result["factors"])


def test_audit_returns_valid_structure():
    profile = load_profile()
    profile_text = profile_to_text(profile)
    result = call_claude(
        build_audit_system_prompt(),
        build_audit_user_message(profile_text),
    )
    assert result["raw_grade"] in ("A", "B", "C", "D")
    assert result["fair_grade"] in ("A", "B", "C", "D")
    assert 0 <= result["raw_score"] <= 100
    assert 0 <= result["fair_score"] <= 100
    assert len(result["signals"]) > 0
    assert result["fair_score"] >= result["raw_score"]
