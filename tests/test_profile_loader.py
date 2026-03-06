import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from profile_loader import load_profile

def test_load_profile_returns_all_sections():
    profile = load_profile()
    assert "name" in profile
    assert "headline" in profile
    assert "summary" in profile
    assert "positions" in profile
    assert "skills" in profile
    assert "education" in profile
    assert "certifications" in profile
    assert "endorsements" in profile
    assert "recommendations" in profile
    assert "industry" in profile
    assert "location" in profile
    assert isinstance(profile["positions"], list)
    assert isinstance(profile["skills"], list)
    assert len(profile["positions"]) > 0
    assert len(profile["skills"]) > 0

def test_position_has_required_fields():
    profile = load_profile()
    pos = profile["positions"][0]
    assert "company" in pos
    assert "title" in pos
    assert "started_on" in pos
    assert "description" in pos
    assert "location" in pos
    assert "finished_on" in pos

def test_name_is_populated():
    profile = load_profile()
    assert profile["name"]["first_name"]
    assert profile["name"]["last_name"]
