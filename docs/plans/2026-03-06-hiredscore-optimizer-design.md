# HiredScore Optimizer Tool — Design Document

**Date:** 2026-03-06
**Status:** Approved

## Problem

AI recruiting systems like HiredScore (now Workday) grade candidates A/B/C/D against job requisitions using opaque algorithms. Candidates have no visibility into how they're scored, what's hurting them, or how bias-prone signals (age proxies, employment gaps, school prestige) affect their ranking.

## Solution

A CLI tool (`hired_score.py`) with three modes:

1. **Score** — Simulate HiredScore grading against a general baseline or specific job description
2. **Audit** — Detect bias-prone signals and show their impact via dual scoring
3. **Advise** — Interactive AI advisor for answering application and interview questions

## Architecture

```
hired_score.py
├── score mode     → Claude API (single call: profile + JD → structured JSON)
├── audit mode     → Claude API (profile → bias analysis JSON)
└── advise mode    → Claude API (interactive loop: question → personalized response)

Shared:
├── profile_loader.py   → Parse LinkedIn CSV export into structured profile dict
└── display.py          → Terminal formatting and colored output
```

### Dependencies

- `anthropic` Python SDK
- `ANTHROPIC_API_KEY` environment variable
- LinkedIn data export in `linkedin_data/` directory

## Scoring Model

Claude evaluates using this weight model, returning 0-100 per factor:

| Factor | Weight | What's Evaluated |
|--------|--------|-----------------|
| Skills/Keywords Match | 40% | Hard skills, tools, technologies vs requirements |
| Experience Relevance | 25% | Role match, years, title progression, company caliber |
| Education/Certs | 10% | Degree, certifications, relevance |
| Recency & Seniority | 10% | How recent is relevant experience, career trajectory |
| Profile Completeness | 10% | Summary, descriptions, quantified achievements |
| Soft Skills/Leadership | 5% | Management, mentoring, cross-functional signals |

**Grade thresholds:** A (80-100), B (60-79), C (40-59), D (0-39)

Based on research into HiredScore's public documentation, the Workday/HiredScore lawsuit disclosures, and industry ATS scoring consensus.

### Two Scoring Modes

- **General mode** (`python hired_score.py score`): Scores profile against an ideal baseline for the candidate's role (SRE/Platform Engineer). Uses LinkedIn export data.
- **Targeted mode** (`python hired_score.py score --job-file posting.txt` or `--job "paste JD"`): Scores profile against a specific job description. Outputs requirement matches, gaps, and how to close them.

## Bias Audit

### Bias-Prone Signals Detected

| Signal | Bias Risk | Mitigation |
|--------|-----------|------------|
| Graduation year | Age proxy | Flag and exclude from scoring |
| Employment gaps | Gender/disability/age | Flag, don't penalize, suggest reframing |
| School name/prestige | Socioeconomic/race proxy | Score degree completion only |
| Outdated job titles | Age proxy | Suggest modern equivalents |
| Location/zip code | Race/socioeconomic proxy | Exclude from scoring |
| "Culture fit" language | Demographic similarity | Flag and suggest alternatives |

### Dual Score Output

Two scores displayed:
- **Raw ATS Score**: How a typical biased ATS would likely grade the candidate
- **Fair Score**: With bias-prone factors removed
- **Bias Impact**: The delta, showing estimated penalty from bias signals

### Adversarial Suggestions

Active recommendations to neutralize bias signals:
- Remove graduation year
- Reframe employment gaps as active pursuits
- Replace outdated titles with modern equivalents
- Add recent activity to counter recency bias

## Advisor Mode

Interactive session that pre-loads the candidate's profile context, then helps craft responses to application and interview questions.

### Profile Context Loaded

- Work history, titles, companies, durations
- Skills and certifications
- Education
- Employment gaps and duration
- Career trajectory and seniority level

### Question Categories Handled

| Category | Examples | Bias Risks Addressed |
|----------|----------|---------------------|
| Free-text app fields | "Why this role?", "Describe yourself" | Age proxies, gap penalties, overqualification |
| Screening questions | "Years of experience with X?" | Knockout filters, seniority bias |
| Salary questions | "Expected compensation?" | Anchoring, pay gap reinforcement |
| Gap explanations | "Account for gaps in employment" | Parenting/disability/age bias |
| Behavioral/interview | "Tell me about a time..." | Recency bias, culture fit proxies |
| Availability | "Start date?", "Relocation?" | Location bias, urgency filtering |

### Advisor Output Format

For each question:
1. What to avoid (with explanation of bias risk)
2. Suggested response (personalized to candidate's actual background)
3. Why the suggestion works
4. Bias signals neutralized

## CLI Interface

```bash
# Score — general baseline
python hired_score.py score

# Score — against specific job description
python hired_score.py score --job-file posting.txt
python hired_score.py score --job "paste JD text here"

# Bias audit
python hired_score.py audit

# Interactive advisor
python hired_score.py advise

# All modes support custom data directory
python hired_score.py score --data-dir /path/to/linkedin_data
```

## File Structure

```
linkedin/
├── hired_score.py          # CLI entrypoint and mode routing
├── profile_loader.py       # LinkedIn CSV parsing into structured dict
├── display.py              # Terminal formatting
├── scoring_prompt.py       # System prompts for scoring mode
├── audit_prompt.py         # System prompts for bias audit mode
├── advisor_prompt.py       # System prompts for advisor mode
├── optimize_profile.py     # Existing profile optimizer (standalone)
├── linkedin_data/          # User's LinkedIn export
└── docs/plans/             # Design docs
```

## Out of Scope

- Web scraping of LinkedIn profiles
- Automatic profile updates
- Database or persistent storage
- Job board integration or automatic job fetching
- Resume PDF parsing (future enhancement)
- GUI / web interface

## Sources

- [HiredScore AI for Recruiting | Workday](https://www.workday.com/en-us/products/talent-management/ai-recruiting.html)
- [AI Hiring Lawsuit — HiredScore Details](https://www.thezerolux.com/ai-hiring-lawsuit-workday-hiredscore/)
- [Workday to Acquire HiredScore — Josh Bersin](https://joshbersin.com/2024/03/workday-to-acquire-hiredscore-a-potential-shakeup-in-hr-technology/)
- [ATS Scoring Logic Guide — Huru.ai](https://huru.ai/ats-resume-ranking-scoring-logic-guide/)
- [Workday & HiredScore Bias Mitigation](https://www.workday.com/en-us/legal/responsible-ai-and-bias-mitigation.html)
