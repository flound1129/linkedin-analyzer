# HiredScore Optimizer — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI tool that simulates HiredScore A/B/C/D grading, detects bias signals, and provides an interactive advisor for application/interview questions.

**Architecture:** CLI entrypoint routes to three modes (score, audit, advise). A shared profile loader parses LinkedIn CSV exports into a structured dict. Each mode has its own Claude API system prompt. The anthropic SDK handles API calls.

**Tech Stack:** Python 3.13, anthropic SDK, venv at `./venv`

**Activate venv before all commands:** `source venv/bin/activate`

---

### Task 1: Profile Loader Module

**Files:**
- Create: `profile_loader.py`
- Create: `tests/test_profile_loader.py`

**Step 1: Write the failing test**

```python
# tests/test_profile_loader.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from profile_loader import load_profile

def test_load_profile_returns_all_sections():
    """Profile loader should return a dict with all expected sections."""
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

def test_name_is_populated():
    profile = load_profile()
    assert profile["name"]["first_name"]
    assert profile["name"]["last_name"]
```

**Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && python -m pytest tests/test_profile_loader.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Write minimal implementation**

```python
# profile_loader.py
"""Parse LinkedIn CSV export into a structured profile dict."""

import csv
import os
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).parent / "linkedin_data"


def _read_csv(filename, data_dir=None):
    """Read a CSV file, returning list of dicts."""
    path = Path(data_dir or DEFAULT_DATA_DIR) / filename
    if not path.exists():
        return []
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _read_connections_csv(data_dir=None):
    """Read Connections.csv which has note lines before the header."""
    path = Path(data_dir or DEFAULT_DATA_DIR) / "Connections.csv"
    if not path.exists():
        return []
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for line in f:
            if line.startswith("First Name,"):
                break
        reader = csv.DictReader(
            f,
            fieldnames=["First Name", "Last Name", "URL", "Email Address",
                        "Company", "Position", "Connected On"],
        )
        for row in reader:
            rows.append(row)
    return rows


def load_profile(data_dir=None):
    """Load all LinkedIn export CSVs into a single structured dict."""
    # Profile basics
    profile_rows = _read_csv("Profile.csv", data_dir)
    p = profile_rows[0] if profile_rows else {}

    # Summary
    summary_rows = _read_csv("Profile Summary.csv", data_dir)
    summary = ""
    if summary_rows:
        summary = summary_rows[0].get("Profile Summary", "")

    # Positions
    positions = []
    for row in _read_csv("Positions.csv", data_dir):
        positions.append({
            "company": row.get("Company Name", ""),
            "title": row.get("Title", ""),
            "description": row.get("Description", ""),
            "location": row.get("Location", ""),
            "started_on": row.get("Started On", ""),
            "finished_on": row.get("Finished On", ""),
        })

    # Skills
    skills = []
    for row in _read_csv("Skills.csv", data_dir):
        name = row.get("Name", "").strip()
        if name:
            skills.append(name)

    # Education
    education = []
    for row in _read_csv("Education.csv", data_dir):
        education.append({
            "school": row.get("School Name", ""),
            "degree": row.get("Degree Name", ""),
            "start_date": row.get("Start Date", ""),
            "end_date": row.get("End Date", ""),
            "activities": row.get("Activities", ""),
        })

    # Certifications
    certifications = []
    for row in _read_csv("Certifications.csv", data_dir):
        certifications.append({
            "name": row.get("Name", ""),
            "authority": row.get("Authority", ""),
            "license_number": row.get("License Number", ""),
        })

    # Endorsements
    endorsements = []
    for row in _read_csv("Endorsement_Received_Info.csv", data_dir):
        endorsements.append({
            "skill": row.get("Skill Name", ""),
            "endorser": f"{row.get('Endorser First Name', '')} {row.get('Endorser Last Name', '')}".strip(),
            "date": row.get("Endorsement Date", ""),
        })

    # Recommendations
    recommendations = []
    for row in _read_csv("Recommendations_Received.csv", data_dir):
        recommendations.append({
            "from": f"{row.get('First Name', '')} {row.get('Last Name', '')}".strip(),
            "company": row.get("Company", ""),
            "title": row.get("Job Title", ""),
            "text": row.get("Text", ""),
        })

    return {
        "name": {
            "first_name": p.get("First Name", ""),
            "last_name": p.get("Last Name", ""),
        },
        "headline": p.get("Headline", ""),
        "summary": summary,
        "industry": p.get("Industry", ""),
        "location": p.get("Geo Location", ""),
        "positions": positions,
        "skills": skills,
        "education": education,
        "certifications": certifications,
        "endorsements": endorsements,
        "recommendations": recommendations,
    }


def profile_to_text(profile):
    """Convert profile dict to a readable text block for Claude prompts."""
    lines = []
    lines.append(f"Name: {profile['name']['first_name']} {profile['name']['last_name']}")
    lines.append(f"Headline: {profile['headline']}")
    lines.append(f"Location: {profile['location']}")
    lines.append(f"Industry: {profile['industry']}")
    lines.append(f"\nSummary:\n{profile['summary'] or '(empty)'}")

    lines.append("\nWork Experience:")
    for pos in profile["positions"]:
        duration = pos["started_on"]
        if pos["finished_on"]:
            duration += f" - {pos['finished_on']}"
        else:
            duration += " - Present"
        lines.append(f"  {pos['title']} at {pos['company']} ({duration})")
        if pos["description"]:
            for desc_line in pos["description"].split("\n"):
                lines.append(f"    {desc_line}")

    lines.append(f"\nSkills ({len(profile['skills'])}):")
    lines.append(f"  {', '.join(profile['skills'])}")

    lines.append("\nEducation:")
    for edu in profile["education"]:
        lines.append(f"  {edu['degree']} - {edu['school']} ({edu['start_date']}-{edu['end_date']})")

    lines.append("\nCertifications:")
    if profile["certifications"]:
        for cert in profile["certifications"]:
            lines.append(f"  {cert['name']} ({cert['authority']})")
    else:
        lines.append("  (none)")

    lines.append(f"\nEndorsements: {len(profile['endorsements'])} total")
    lines.append(f"Recommendations: {len(profile['recommendations'])} total")
    if profile["recommendations"]:
        for rec in profile["recommendations"]:
            lines.append(f"  From {rec['from']} ({rec['title']} at {rec['company']}):")
            lines.append(f"    \"{rec['text'][:200]}...\"" if len(rec['text']) > 200 else f"    \"{rec['text']}\"")

    return "\n".join(lines)
```

**Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && python -m pytest tests/test_profile_loader.py -v`
Expected: 3 PASSED

**Step 5: Commit**

```bash
git add tests/test_profile_loader.py profile_loader.py
git commit -m "feat: add profile loader for LinkedIn CSV export"
```

---

### Task 2: Display Module

**Files:**
- Create: `display.py`

**Step 1: Write implementation**

No test needed — pure formatting output.

```python
# display.py
"""Terminal formatting for HiredScore output."""

import sys


def _supports_color():
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


USE_COLOR = _supports_color()


def _color(text, code):
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def red(text):
    return _color(text, "31")


def green(text):
    return _color(text, "32")


def yellow(text):
    return _color(text, "33")


def blue(text):
    return _color(text, "34")


def bold(text):
    return _color(text, "1")


def grade_color(grade):
    """Color a grade letter."""
    colors = {"A": green, "B": blue, "C": yellow, "D": red}
    return colors.get(grade, lambda x: x)(grade)


def bar(value, max_value, width=20):
    """Render a progress bar."""
    filled = int(width * value / max(max_value, 1))
    return green("#" * filled) + red("-" * (width - filled))


def header(text):
    """Print a section header."""
    line = "=" * 60
    print(f"\n{bold(line)}")
    print(f"  {bold(text)}")
    print(bold(line))


def print_score_breakdown(result):
    """Print the full scoring breakdown from Claude's JSON response."""
    grade = result["grade"]
    total = result["total_score"]

    header(f"HIREDSCORE SIMULATION — Grade: {grade_color(grade)} ({total}/100)")

    print(f"\n  {bold('Factor Breakdown:')}\n")
    for factor in result["factors"]:
        name = factor["name"]
        score = factor["score"]
        max_score = factor["max_score"]
        comment = factor["comment"]
        print(f"    {name:<25s} {bar(score, max_score)} {score}/{max_score}  {comment}")

    if result.get("improvements"):
        print(f"\n  {bold('Top Improvements:')}\n")
        for i, imp in enumerate(result["improvements"], 1):
            pts = imp.get("estimated_points", "?")
            print(f"    {i}. {imp['action']} ({green(f'+{pts} pts')})")

    if result.get("suggested_rewrites"):
        print(f"\n  {bold('Suggested Rewrites:')}\n")
        for rw in result["suggested_rewrites"]:
            print(f"    >> {bold(rw['section'])}\n")
            for line in rw["text"].split("\n"):
                print(f"    {line}")
            print()


def print_bias_audit(result):
    """Print bias audit results."""
    raw = result["raw_score"]
    fair = result["fair_score"]
    delta = fair - raw

    header("BIAS AUDIT")
    print(f"\n  Raw ATS Score:   {grade_color(result['raw_grade'])} ({raw}/100)")
    print(f"  Fair Score:      {grade_color(result['fair_grade'])} ({fair}/100)")
    print(f"  Bias Impact:     {red(f'{delta:+d} pts') if delta > 0 else f'{delta:+d} pts'}")

    print(f"\n  {bold('Signals Detected:')}\n")
    for signal in result["signals"]:
        status = yellow("!") if signal["detected"] else green("ok")
        impact = red(f"{signal['impact']:+d} pts") if signal["impact"] else green("no impact")
        print(f"    [{status}] {signal['name']:<35s} {impact}")
        if signal.get("detail"):
            print(f"        {signal['detail']}")

    if result.get("adversarial_suggestions"):
        print(f"\n  {bold('Adversarial Suggestions:')}\n")
        for i, sug in enumerate(result["adversarial_suggestions"], 1):
            print(f"    {i}. {sug}")


def print_advisor_response(response):
    """Print advisor response for a question."""
    print(f"\n  {bold('Avoid:')}")
    for avoid in response.get("avoid", []):
        print(f"    {red('x')} {avoid['text']}")
        if avoid.get("reason"):
            print(f"      Reason: {avoid['reason']}")

    print(f"\n  {bold('Suggested Response:')}")
    print()
    for line in response["suggested_response"].split("\n"):
        print(f"    {green('|')} {line}")

    if response.get("why_it_works"):
        print(f"\n  {bold('Why this works:')}")
        print(f"    {response['why_it_works']}")

    if response.get("bias_signals_neutralized"):
        print(f"\n  {bold('Bias signals neutralized:')}")
        for sig in response["bias_signals_neutralized"]:
            print(f"    {green('ok')} {sig}")
```

**Step 2: Commit**

```bash
git add display.py
git commit -m "feat: add display module for terminal formatting"
```

---

### Task 3: Scoring Prompt Module

**Files:**
- Create: `scoring_prompt.py`
- Create: `tests/test_scoring_prompt.py`

**Step 1: Write the failing test**

```python
# tests/test_scoring_prompt.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scoring_prompt import build_scoring_system_prompt, build_scoring_user_message

def test_system_prompt_contains_weight_model():
    prompt = build_scoring_system_prompt()
    assert "40%" in prompt  # skills weight
    assert "25%" in prompt  # experience weight
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
```

**Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && python -m pytest tests/test_scoring_prompt.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# scoring_prompt.py
"""System prompts for HiredScore scoring mode."""

SCORING_SYSTEM_PROMPT = """\
You are an AI recruiting system simulator modeled after HiredScore/Workday's \
candidate grading system. You evaluate candidate profiles against job requirements \
and assign an A/B/C/D grade.

## Scoring Model

Evaluate the candidate on these factors, scoring each from 0 to its max:

| Factor                  | Max Score | Weight | What to Evaluate |
|-------------------------|-----------|--------|------------------|
| Skills/Keywords Match   | 40        | 40%    | Hard skills, tools, technologies matching requirements |
| Experience Relevance    | 25        | 25%    | Role match, years of experience, title progression, company caliber |
| Education/Certifications| 10        | 10%    | Degree relevance, certifications, continuing education |
| Recency & Seniority     | 10        | 10%    | How recent is relevant experience, career trajectory direction |
| Profile Completeness    | 10        | 10%    | Summary/about section, position descriptions, quantified achievements |
| Soft Skills/Leadership  | 5         | 5%     | Management, mentoring, cross-functional work, communication signals |

## Grade Thresholds
- A: 80-100 (strong match)
- B: 60-79 (good match with gaps)
- C: 40-59 (partial match)
- D: 0-39 (poor match)

## Scoring Rules
- Score based ONLY on what is stated in the profile. Do not assume skills not listed.
- Missing sections (empty summary, no position descriptions) should be penalized under Profile Completeness.
- For targeted scoring, extract requirements from the job description and match explicitly.
- For general scoring, evaluate against industry best practices for the candidate's stated role.

## Output Format

Respond with ONLY valid JSON (no markdown, no code fences):

{
  "grade": "B",
  "total_score": 68,
  "factors": [
    {"name": "Skills/Keywords Match", "score": 32, "max_score": 40, "comment": "brief explanation"},
    {"name": "Experience Relevance", "score": 20, "max_score": 25, "comment": "brief explanation"},
    {"name": "Education/Certifications", "score": 6, "max_score": 10, "comment": "brief explanation"},
    {"name": "Recency & Seniority", "score": 5, "max_score": 10, "comment": "brief explanation"},
    {"name": "Profile Completeness", "score": 3, "max_score": 10, "comment": "brief explanation"},
    {"name": "Soft Skills/Leadership", "score": 2, "max_score": 5, "comment": "brief explanation"}
  ],
  "improvements": [
    {"action": "what to do", "estimated_points": 5},
    {"action": "what to do", "estimated_points": 3}
  ],
  "suggested_rewrites": [
    {"section": "Summary", "text": "suggested rewrite text"},
    {"section": "Pinterest - SRE", "text": "suggested bullet points"}
  ]
}
"""


def build_scoring_system_prompt():
    return SCORING_SYSTEM_PROMPT


def build_scoring_user_message(profile_text, job_description=None):
    if job_description:
        return (
            f"Score this candidate profile against the following job description.\n\n"
            f"## Job Description\n\n{job_description}\n\n"
            f"## Candidate Profile\n\n{profile_text}"
        )
    return (
        f"Score this candidate profile against a general baseline for their stated role. "
        f"Evaluate how well-optimized this profile is for AI recruiting systems.\n\n"
        f"## Candidate Profile\n\n{profile_text}"
    )
```

**Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && python -m pytest tests/test_scoring_prompt.py -v`
Expected: 4 PASSED

**Step 5: Commit**

```bash
git add scoring_prompt.py tests/test_scoring_prompt.py
git commit -m "feat: add scoring prompt module with weight model"
```

---

### Task 4: Bias Audit Prompt Module

**Files:**
- Create: `audit_prompt.py`
- Create: `tests/test_audit_prompt.py`

**Step 1: Write the failing test**

```python
# tests/test_audit_prompt.py
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
```

**Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && python -m pytest tests/test_audit_prompt.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# audit_prompt.py
"""System prompts for bias audit mode."""

AUDIT_SYSTEM_PROMPT = """\
You are a bias detection system for AI recruiting tools. Analyze a candidate's \
resume/profile and identify signals that may trigger unfair bias in AI scoring \
systems like HiredScore/Workday.

## Bias-Prone Signals to Detect

1. **Graduation Year as Age Proxy**: If education dates are present, they reveal \
approximate age. Flag and estimate scoring penalty.
2. **Employment Gaps**: Gaps between positions may penalize candidates unfairly \
(parenting, disability, career transition). Flag each gap with duration.
3. **School Name/Prestige**: Elite school names may inflate scores; unknown schools \
may deflate them. Flag if school prestige is likely a factor.
4. **Outdated Job Titles**: Titles like "Systems Administrator", "Webmaster", \
"Client Engineer" signal older career start. Suggest modern equivalents.
5. **Location/Zip Code**: Geographic data can correlate with demographics. Flag if present.
6. **Legacy Technologies**: Listing only outdated tech (Solaris, Perl, WebSphere) \
without modern equivalents signals age. Flag specific legacy skills.

## Dual Scoring

Provide TWO scores:
- **raw_score**: How a typical ATS with these biases would score this candidate (0-100)
- **fair_score**: Score based purely on skills, experience quality, and achievements \
with bias-prone factors removed (0-100)

## Output Format

Respond with ONLY valid JSON (no markdown, no code fences):

{
  "raw_score": 52,
  "raw_grade": "C",
  "fair_score": 71,
  "fair_grade": "B",
  "signals": [
    {
      "name": "Graduation Year (Age Proxy)",
      "detected": true,
      "impact": -6,
      "detail": "Graduation year 1998 suggests candidate is ~50, triggering age bias"
    },
    {
      "name": "Employment Gap",
      "detected": true,
      "impact": -8,
      "detail": "4-year gap from 2022-present flagged as inactive"
    },
    {
      "name": "School Prestige",
      "detected": false,
      "impact": 0,
      "detail": null
    },
    {
      "name": "Outdated Job Titles",
      "detected": true,
      "impact": -3,
      "detail": "'Sr Systems Administrator' and 'Client Engineer' signal legacy career"
    },
    {
      "name": "Location Bias",
      "detected": false,
      "impact": 0,
      "detail": null
    },
    {
      "name": "Legacy Technologies",
      "detected": true,
      "impact": -2,
      "detail": "Solaris, WebSphere, Oracle Application Server listed without modern equivalents"
    }
  ],
  "adversarial_suggestions": [
    "Remove graduation year from education section",
    "Add 'Angel Investor & AI Developer (2022-Present)' to close employment gap",
    "Retitle 'Sr Systems Administrator' to 'Infrastructure Engineer'",
    "Retitle 'Client Engineer' to 'Solutions Engineer'",
    "Add Kubernetes, Docker, Terraform to skills if experienced"
  ]
}
"""


def build_audit_system_prompt():
    return AUDIT_SYSTEM_PROMPT


def build_audit_user_message(profile_text):
    return (
        f"Analyze this candidate profile for bias-prone signals that AI recruiting "
        f"systems may use unfairly. Provide dual scoring and adversarial suggestions.\n\n"
        f"## Candidate Profile\n\n{profile_text}"
    )
```

**Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && python -m pytest tests/test_audit_prompt.py -v`
Expected: 2 PASSED

**Step 5: Commit**

```bash
git add audit_prompt.py tests/test_audit_prompt.py
git commit -m "feat: add bias audit prompt module"
```

---

### Task 5: Advisor Prompt Module

**Files:**
- Create: `advisor_prompt.py`
- Create: `tests/test_advisor_prompt.py`

**Step 1: Write the failing test**

```python
# tests/test_advisor_prompt.py
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
```

**Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && python -m pytest tests/test_advisor_prompt.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
# advisor_prompt.py
"""System prompts for interactive advisor mode."""


def build_advisor_system_prompt(profile_text):
    return f"""\
You are a career advisor specializing in helping candidates navigate AI-powered \
hiring systems and avoid triggering algorithmic bias. You have deep knowledge of \
how ATS systems like HiredScore, Workday, Greenhouse, and Lever score candidates.

## Candidate Context

The following is the candidate's full profile. Use this to personalize all responses \
with their actual experience, companies, skills, and career trajectory:

{profile_text}

## Your Role

When the candidate pastes a question from a job application, screening form, or \
interview prep, you help them craft a response that:

1. Is completely honest and accurate to their background
2. Avoids triggering common bias signals in AI systems
3. Maximizes their score in keyword/skills matching
4. Frames their experience positively

## Bias Signals to Help Avoid

- **Age proxies**: Don't reference graduation year, "25+ years experience", or date-specific technology
- **Employment gaps**: Reframe as intentional career moves, not periods of inactivity
- **Overqualification**: Don't undersell, but frame experience as directly relevant
- **Salary anchoring**: Guide toward deferring or researching market rate
- **Location bias**: Focus on remote capability or willingness to relocate
- **Culture fit traps**: Use inclusive, professional language

## Output Format

Respond with ONLY valid JSON (no markdown, no code fences):

{{
  "avoid": [
    {{"text": "what not to say", "reason": "why it triggers bias"}}
  ],
  "suggested_response": "the crafted response text",
  "why_it_works": "explanation of the strategy",
  "bias_signals_neutralized": ["signal 1", "signal 2"]
}}
"""


def build_advisor_user_message(question):
    return (
        f"Help me answer this question from a job application or interview. "
        f"Craft a response that is honest, highlights my strengths, and avoids "
        f"triggering AI bias signals.\n\n"
        f"Question: {question}"
    )
```

**Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && python -m pytest tests/test_advisor_prompt.py -v`
Expected: 2 PASSED

**Step 5: Commit**

```bash
git add advisor_prompt.py tests/test_advisor_prompt.py
git commit -m "feat: add advisor prompt module"
```

---

### Task 6: CLI Entrypoint

**Files:**
- Create: `hired_score.py`
- Create: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
# tests/test_cli.py
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
```

**Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && python -m pytest tests/test_cli.py -v`
Expected: FAIL

**Step 3: Write implementation**

```python
#!/usr/bin/env python3
"""HiredScore Optimizer — Simulate AI recruiting scores, detect bias, get advice."""

import argparse
import json
import os
import sys

import anthropic

from profile_loader import load_profile, profile_to_text
from display import (
    header, print_score_breakdown, print_bias_audit,
    print_advisor_response, bold, green, yellow, red,
)
from scoring_prompt import build_scoring_system_prompt, build_scoring_user_message
from audit_prompt import build_audit_system_prompt, build_audit_user_message
from advisor_prompt import build_advisor_system_prompt, build_advisor_user_message

MODEL = "claude-sonnet-4-6"


def get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is required.", file=sys.stderr)
        print("Set it with: export ANTHROPIC_API_KEY=your-key-here", file=sys.stderr)
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)


def call_claude(client, system_prompt, user_message):
    """Call Claude API and parse JSON response."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    text = response.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
    return json.loads(text)


def cmd_score(args):
    """Score mode: simulate HiredScore grading."""
    client = get_client()
    profile = load_profile(args.data_dir)
    profile_text = profile_to_text(profile)

    job_description = None
    if args.job_file:
        with open(args.job_file) as f:
            job_description = f.read()
    elif args.job:
        job_description = args.job

    system_prompt = build_scoring_system_prompt()
    user_message = build_scoring_user_message(profile_text, job_description)

    print("\nAnalyzing profile", end="")
    if job_description:
        print(" against job description", end="")
    print("...\n")

    result = call_claude(client, system_prompt, user_message)
    print_score_breakdown(result)


def cmd_audit(args):
    """Audit mode: detect bias signals."""
    client = get_client()
    profile = load_profile(args.data_dir)
    profile_text = profile_to_text(profile)

    system_prompt = build_audit_system_prompt()
    user_message = build_audit_user_message(profile_text)

    print("\nRunning bias audit...\n")

    result = call_claude(client, system_prompt, user_message)
    print_bias_audit(result)


def cmd_advise(args):
    """Advise mode: interactive advisor session."""
    client = get_client()
    profile = load_profile(args.data_dir)
    profile_text = profile_to_text(profile)

    system_prompt = build_advisor_system_prompt(profile_text)

    name = f"{profile['name']['first_name']} {profile['name']['last_name']}"
    headline = profile["headline"]

    header("HIREDSCORE ADVISOR")
    print(f"\n  Profile loaded: {bold(name)} — {headline}")
    print(f"  Type a question from an application or interview.")
    print(f"  Type {bold('quit')} or {bold('exit')} to end.\n")

    while True:
        try:
            question = input(f"  {bold('You:')} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            break

        user_message = build_advisor_user_message(question)
        print(f"\n  {yellow('Thinking...')}\n")

        result = call_claude(client, system_prompt, user_message)
        print_advisor_response(result)
        print()


def main():
    parser = argparse.ArgumentParser(
        description="HiredScore Optimizer — Simulate AI recruiting scores, detect bias, get advice.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  %(prog)s score                          General profile score
  %(prog)s score --job-file posting.txt   Score against a job description
  %(prog)s audit                          Detect bias signals
  %(prog)s advise                         Interactive advisor
        """,
    )
    parser.add_argument("--data-dir", default=None, help="Path to LinkedIn data export directory")

    subparsers = parser.add_subparsers(dest="command")

    # Score
    score_parser = subparsers.add_parser("score", help="Simulate HiredScore grading")
    score_parser.add_argument("--job-file", help="Path to job description file")
    score_parser.add_argument("--job", help="Job description text")
    score_parser.add_argument("--data-dir", default=None)

    # Audit
    audit_parser = subparsers.add_parser("audit", help="Detect bias-prone signals")
    audit_parser.add_argument("--data-dir", default=None)

    # Advise
    advise_parser = subparsers.add_parser("advise", help="Interactive advisor")
    advise_parser.add_argument("--data-dir", default=None)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "score":
        cmd_score(args)
    elif args.command == "audit":
        cmd_audit(args)
    elif args.command == "advise":
        cmd_advise(args)


if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && python -m pytest tests/test_cli.py -v`
Expected: 2 PASSED

**Step 5: Commit**

```bash
git add hired_score.py tests/test_cli.py
git commit -m "feat: add CLI entrypoint with score, audit, advise modes"
```

---

### Task 7: Integration Test — Score Mode

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test (requires API key)**

```python
# tests/test_integration.py
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
```

**Step 2: Run integration tests**

Run: `source venv/bin/activate && python -m pytest tests/test_integration.py -v`
Expected: 2 PASSED (or SKIPPED if no API key)

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for score and audit modes"
```

---

### Task 8: Build Script

**Files:**
- Create: `scripts/test.sh`

**Step 1: Write the script**

```bash
#!/usr/bin/env bash
# Run all tests for the HiredScore optimizer
set -euo pipefail
cd "$(dirname "$0")/.."
source venv/bin/activate
echo "Running unit tests..."
python -m pytest tests/ -v --ignore=tests/test_integration.py
echo ""
echo "Running integration tests (requires ANTHROPIC_API_KEY)..."
python -m pytest tests/test_integration.py -v
```

**Step 2: Make executable and run**

Run: `chmod +x scripts/test.sh && scripts/test.sh`
Expected: All tests pass

**Step 3: Commit**

```bash
git add scripts/test.sh
git commit -m "chore: add test runner script"
```

---

### Task 9: End-to-End Smoke Test

**Step 1: Run score mode**

Run: `source venv/bin/activate && python hired_score.py score`
Expected: Full scoring output with A/B/C/D grade and breakdown

**Step 2: Run audit mode**

Run: `source venv/bin/activate && python hired_score.py audit`
Expected: Bias audit with dual scores and suggestions

**Step 3: Verify advisor mode starts**

Run: `echo "Why did you leave Pinterest?" | source venv/bin/activate && python hired_score.py advise`
Expected: Advisor loads profile and responds to the question

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: HiredScore optimizer tool — score, audit, advise modes complete"
```
