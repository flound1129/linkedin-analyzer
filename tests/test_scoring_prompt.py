import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scoring_prompt import build_scoring_system_prompt, build_scoring_user_message

def test_system_prompt_contains_weight_model():
    prompt = build_scoring_system_prompt()
    assert "40%" in prompt
    assert "25%" in prompt
    assert "A/B/C/D" in prompt or "A, B, C, D" in prompt

def test_user_message_contains_profile():
    profile_text = "Name: Test User\nHeadline: Engineer"
    msg = build_scoring_user_message(profile_text)
    assert "Test User" in msg

def test_user_message_with_job_description():
    profile_text = "Name: Test User"
    jd = "We are looking for a Senior SRE"
    msg = build_scoring_user_message(profile_text, job_description=jd)
    assert "Senior SRE" in msg
    assert "Test User" in msg

def test_user_message_without_job_uses_general():
    profile_text = "Name: Test User"
    msg = build_scoring_user_message(profile_text)
    assert "general" in msg.lower() or "baseline" in msg.lower()
