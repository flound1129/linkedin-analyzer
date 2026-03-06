import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advisor_prompt import build_advisor_system_prompt, build_advisor_user_message

def test_system_prompt_contains_bias_guidance():
    prompt = build_advisor_system_prompt("Name: Test User\nHeadline: SRE")
    assert "bias" in prompt.lower()
    assert "Test User" in prompt

def test_user_message_contains_question():
    msg = build_advisor_user_message("Why did you leave your last job?")
    assert "Why did you leave" in msg
