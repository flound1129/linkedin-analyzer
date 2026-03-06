# HiredScore Optimizer — Scoring Strategy

## Background

HiredScore (acquired by Workday in 2024) is an AI recruiting system used by large enterprises to grade candidates A/B/C/D against job requisitions. The algorithm is proprietary, but through public documentation, the Workday/HiredScore lawsuit disclosures, and industry ATS research, we've reverse-engineered a scoring model that approximates how these systems evaluate candidates.

### Key Findings From Research

- HiredScore assigns **A/B/C/D grades** based on how well a candidate's CV matches skills, education, and experience in the job description
- Scores are **not curved** — they're absolute match scores per requisition, not relative to other candidates
- The system examines **work history, keyword alignment, title progression, and inferred skill sets**
- Scores below a threshold can result in **automatic filtering** before a human ever sees the application
- Despite claims of fairness, the system can use **proxy signals** (graduation year, employment gaps, outdated titles) that correlate with protected characteristics like age, gender, and race

## Scoring Model

Our tool evaluates candidates across six weighted factors totaling 100 points:

| Factor | Max Points | Weight | What's Evaluated |
|--------|-----------|--------|-----------------|
| Skills/Keywords Match | 40 | 40% | Hard skills, tools, technologies vs. requirements |
| Experience Relevance | 25 | 25% | Role match, years, title progression, company caliber |
| Education/Certifications | 10 | 10% | Degree, certifications, continuing education |
| Recency & Seniority | 10 | 10% | How recent is relevant experience, career trajectory |
| Profile Completeness | 10 | 10% | Summary, descriptions, quantified achievements |
| Soft Skills/Leadership | 5 | 5% | Management, mentoring, cross-functional signals |

### Why These Weights

**Skills/Keywords at 40%** is the dominant factor because ATS research consistently shows keyword matching accounts for the largest share of candidate scoring. Multiple sources (Huru.ai, Cutshort, Jobscan) converge on 35-45% for keyword/skills matching. HiredScore's own documentation emphasizes matching "skills and experience" against requisition requirements.

**Experience Relevance at 25%** reflects that ATS systems heavily weight work history — not just that you have skills, but that you've applied them in relevant roles at recognizable companies. Title progression and company caliber are strong signals.

**Education/Certifications at 10%** is weighted lower than skills and experience because research shows ATS systems treat education as "medium priority" compared to skills sections ("very high") and work experience ("very high"). However, certifications carry outsized weight for technical roles.

**Recency & Seniority at 10%** captures the ATS behavior of weighting recent experience more heavily. A skill used last year scores higher than one used a decade ago. Career trajectory direction also matters — are you trending up or plateauing?

**Profile Completeness at 10%** penalizes missing sections. An empty summary, blank position descriptions, or lack of quantified achievements all reduce the data available for the AI to match against. Less data means lower scores.

**Soft Skills/Leadership at 5%** has the lowest weight because ATS systems are poor at evaluating soft skills from text. However, signals like team size, mentoring language, and cross-functional collaboration do register.

### Grade Thresholds

| Grade | Score Range | Meaning |
|-------|------------|---------|
| A | 80-100 | Strong match — profile aligns closely with requirements |
| B | 60-79 | Good match with gaps — most requirements met, some missing |
| C | 40-59 | Partial match — significant gaps in skills or experience |
| D | 0-39 | Poor match — does not meet core requirements |

These thresholds mirror HiredScore's own A/B/C/D system. Per their documentation, grades are absolute (not curved against other candidates), meaning a requisition with common requirements may produce many As while a niche requisition may produce mostly Cs and Ds.

## Two Scoring Modes

### General Mode

Scores a profile against an ideal baseline for the candidate's stated role. Evaluates how well-optimized the profile is for AI recruiting systems in general. Useful for identifying profile weaknesses before targeting specific jobs.

### Targeted Mode

Scores a profile against a specific job description. The AI extracts requirements from the JD and matches them explicitly against the candidate's profile. Outputs which requirements are met, which are missing, and how to close gaps. This simulates what happens when an actual ATS processes your application.

## Bias Audit Layer

### The Problem

The Workday/HiredScore lawsuit revealed that even AI systems designed to exclude demographic indicators can replicate structural bias through proxy signals. Our bias audit detects these signals and quantifies their impact.

### Bias-Prone Signals

| Signal | How It Creates Bias | Our Mitigation |
|--------|-------------------|----------------|
| Graduation year | Reveals approximate age — penalizes older candidates | Flagged, excluded from fair score |
| Employment gaps | Disproportionately affects women (parenting), disabled, older workers | Flagged, not penalized in fair score, reframing suggested |
| School prestige | Correlates with socioeconomic status and race | Fair score uses degree completion only |
| Outdated job titles | "Systems Administrator" signals older career start | Modern equivalents suggested |
| Location/zip code | Correlates with race and socioeconomic status | Excluded from scoring |
| Legacy technologies | Listing Solaris/WebSphere without modern equivalents signals age | Removal or de-prioritization suggested |
| Career span | 25+ year career history triggers implicit age bias | Truncation strategies suggested |

### Dual Score

We produce two scores:

- **Raw ATS Score** — How a typical biased ATS would likely grade the candidate, including penalties from proxy signals
- **Fair Score** — Score based purely on skills, experience quality, and achievements with bias-prone factors removed

The delta between these scores quantifies the **estimated bias impact** on the candidate's real-world applications.

### Adversarial Suggestions

Beyond detection, we provide actionable steps to neutralize bias signals while remaining truthful:

- Remove graduation years from education
- Reframe employment gaps as active pursuits (consulting, investing, projects)
- Replace outdated job titles with modern equivalents
- Remove or de-prioritize legacy technology skills
- Add recent activity to counter recency bias

## Scoring Rules

1. **Score only what is stated.** Do not assume skills not listed. If Kubernetes isn't mentioned, it scores zero even if the candidate likely used it.
2. **Penalize missing sections.** An empty summary or blank position descriptions reduce the data available for matching.
3. **Context matters more than keyword counting.** A skill mentioned in a quantified achievement ("reduced MTTR by 40% using Prometheus") scores higher than a skill listed in isolation.
4. **Hidden keyword stuffing is penalized.** Modern AI systems detect invisible or out-of-context keyword blocks and flag them as manipulation.
5. **Targeted scoring extracts requirements explicitly.** When scoring against a job description, requirements are extracted and matched one-by-one.
6. **Quantified achievements boost scores.** Numbers, percentages, and scale indicators (users served, hosts managed, revenue impact) carry more weight than unquantified bullets.

## Sources

- [HiredScore AI for Recruiting | Workday](https://www.workday.com/en-us/products/talent-management/ai-recruiting.html)
- [AI Hiring Lawsuit — Workday/HiredScore](https://www.thezerolux.com/ai-hiring-lawsuit-workday-hiredscore/)
- [Workday to Acquire HiredScore — Josh Bersin](https://joshbersin.com/2024/03/workday-to-acquire-hiredscore-a-potential-shakeup-in-hr-technology/)
- [Workday & HiredScore Bias Mitigation](https://www.workday.com/en-us/legal/responsible-ai-and-bias-mitigation.html)
- [ATS Resume Ranking and Scoring Logic — Huru.ai](https://huru.ai/ats-resume-ranking-scoring-logic-guide/)
- [Understanding ATS Scoring Algorithms — Scale.jobs](https://scale.jobs/blog/understanding-ats-scoring-algorithms)
- [How ATS Score is Calculated — Cutshort](https://cutshort.io/blog/job-search-insights/how-resume-ats-score-is-calculated-by-ai-in-2025)
