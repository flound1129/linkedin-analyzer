import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit_prompt import build_audit_system_prompt, build_audit_user_message

def test_system_prompt_mentions_bias_signals():
    prompt = build_audit_system_prompt()
    assert "graduation year" in prompt.lower() or "age proxy" in prompt.lower()
    assert "employment gap" in prompt.lower()
    assert "raw" in prompt.lower() and "fair" in prompt.lower()

def test_user_message_contains_profile():
    msg = build_audit_user_message("Name: Test User")
    assert "Test User" in msg
