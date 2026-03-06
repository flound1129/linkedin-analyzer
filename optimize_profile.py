#!/usr/bin/env python3
"""LinkedIn Profile Optimizer - Analyze your LinkedIn data export and get
actionable recommendations to improve your visibility to AI recruiting
systems like HiredScore/Workday."""

import csv
import os
from collections import Counter
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "linkedin_data")


def read_csv(filename, skip_notes=False):
    """Read a CSV file from the data directory, returning list of dicts."""
    path = os.path.join(DATA_DIR, filename)
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        if skip_notes:
            # Connections.csv has note lines before the header
            for line in f:
                if line.startswith("First Name,"):
                    break
            reader = csv.DictReader(f, fieldnames=line.strip().split(","))
        else:
            reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_profile():
    rows = read_csv("Profile.csv")
    return rows[0] if rows else {}


def load_positions():
    return read_csv("Positions.csv")


def load_skills():
    return read_csv("Skills.csv")


def load_education():
    return read_csv("Education.csv")


def load_certifications():
    return read_csv("Certifications.csv")


def load_endorsements():
    return read_csv("Endorsement_Received_Info.csv")


def load_recommendations():
    return read_csv("Recommendations_Received.csv")


def load_summary():
    rows = read_csv("Profile Summary.csv")
    return rows[0].get("Profile Summary", "") if rows else ""


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def analyze_completeness(profile, summary, positions, skills, education, certs, endorsements, recs):
    """Score profile completeness across key fields that AI recruiters weight."""
    scores = {}
    max_points = 0

    # Headline (10 pts)
    max_points += 10
    headline = profile.get("Headline", "")
    if len(headline) > 100:
        scores["Headline"] = (10, "Strong headline with keywords")
    elif len(headline) > 50:
        scores["Headline"] = (7, "Decent headline, could add more keywords")
    elif headline:
        scores["Headline"] = (4, f"Short headline ({len(headline)} chars) - aim for 120+ chars with role keywords")
    else:
        scores["Headline"] = (0, "Missing headline")

    # Summary / About (15 pts)
    max_points += 15
    if len(summary) > 500:
        scores["Summary/About"] = (15, "Detailed summary")
    elif len(summary) > 200:
        scores["Summary/About"] = (10, "Summary could be longer - aim for 500+ chars")
    elif summary.strip():
        scores["Summary/About"] = (5, "Summary is too brief")
    else:
        scores["Summary/About"] = (0, "EMPTY - This is the #1 field AI recruiters parse")

    # Positions (20 pts)
    max_points += 20
    described = sum(1 for p in positions if p.get("Description", "").strip())
    total = len(positions)
    if total == 0:
        scores["Positions"] = (0, "No positions listed")
    else:
        ratio = described / total
        pts = int(20 * ratio)
        scores["Positions"] = (pts, f"{described}/{total} positions have descriptions")

    # Skills (10 pts)
    max_points += 10
    skill_count = len(skills)
    if skill_count >= 50:
        scores["Skills"] = (10, f"Maximum skills listed ({skill_count})")
    elif skill_count >= 30:
        scores["Skills"] = (7, f"{skill_count}/50 skills - add {50 - skill_count} more")
    elif skill_count > 0:
        scores["Skills"] = (4, f"Only {skill_count}/50 skills listed")
    else:
        scores["Skills"] = (0, "No skills listed")

    # Education (5 pts)
    max_points += 5
    if education:
        has_details = any(e.get("Degree Name", "").strip() for e in education)
        scores["Education"] = (5 if has_details else 3, f"{len(education)} entries")
    else:
        scores["Education"] = (0, "No education listed")

    # Certifications (5 pts)
    max_points += 5
    if len(certs) >= 3:
        scores["Certifications"] = (5, f"{len(certs)} certifications")
    elif certs:
        scores["Certifications"] = (2, f"Only {len(certs)} certification(s) - add more")
    else:
        scores["Certifications"] = (0, "No certifications")

    # Endorsements (5 pts)
    max_points += 5
    unique_endorsers = len(set(
        f"{e.get('Endorser First Name', '')} {e.get('Endorser Last Name', '')}"
        for e in endorsements
    ))
    if unique_endorsers >= 20:
        scores["Endorsements"] = (5, f"{unique_endorsers} unique endorsers")
    elif unique_endorsers >= 10:
        scores["Endorsements"] = (3, f"{unique_endorsers} unique endorsers - ask more connections")
    elif unique_endorsers > 0:
        scores["Endorsements"] = (2, f"Only {unique_endorsers} unique endorsers")
    else:
        scores["Endorsements"] = (0, "No endorsements")

    # Recommendations (5 pts)
    max_points += 5
    if len(recs) >= 5:
        scores["Recommendations"] = (5, f"{len(recs)} recommendations")
    elif len(recs) >= 3:
        scores["Recommendations"] = (3, f"{len(recs)} recommendations - aim for 5+")
    elif recs:
        scores["Recommendations"] = (1, f"Only {len(recs)} recommendation(s) - ask former colleagues")
    else:
        scores["Recommendations"] = (0, "No recommendations")

    # Recent activity (5 pts) - proxy: most recent endorsement date
    max_points += 5
    if endorsements:
        latest = max(e.get("Endorsement Date", "") for e in endorsements)
        try:
            latest_dt = datetime.strptime(latest[:10], "%Y/%m/%d")
            age_days = (datetime.now() - latest_dt).days
            if age_days < 180:
                scores["Recent Activity"] = (5, f"Recent endorsement ({latest[:10]})")
            elif age_days < 365:
                scores["Recent Activity"] = (3, f"Last endorsement {age_days} days ago")
            else:
                scores["Recent Activity"] = (1, f"Last endorsement {age_days} days ago - profile looks stale")
        except ValueError:
            scores["Recent Activity"] = (1, "Could not parse endorsement dates")
    else:
        scores["Recent Activity"] = (0, "No recent activity signal")

    return scores, max_points


def analyze_skills_gap(skills):
    """Compare listed skills against in-demand skills for SRE/Platform/DevOps roles."""
    current_skills = set(s.get("Name", "").lower() for s in skills)

    # Skills commonly sought for SRE / Platform / DevOps roles in 2025-2026
    in_demand = {
        "Kubernetes": ["kubernetes", "k8s"],
        "Docker / Containers": ["docker", "containers", "containerization"],
        "Terraform": ["terraform"],
        "Infrastructure as Code": ["infrastructure as code", "iac"],
        "CI/CD": ["ci/cd", "continuous integration", "continuous delivery"],
        "Go / Golang": ["go", "golang"],
        "TypeScript": ["typescript"],
        "Observability": ["observability", "monitoring"],
        "Prometheus / Grafana": ["prometheus", "grafana"],
        "Datadog": ["datadog"],
        "Incident Management": ["incident management", "incident response"],
        "SLOs / SLIs": ["slo", "sli", "service level"],
        "Microservices": ["microservices"],
        "gRPC": ["grpc"],
        "Apache Kafka": ["kafka"],
        "Elasticsearch": ["elasticsearch"],
        "Git": ["git"],
        "Ansible": ["ansible"],
        "Puppet / Chef": ["puppet", "chef"],
        "Nginx": ["nginx"],
        "Load Balancing": ["load balancing"],
        "Networking (TCP/IP, DNS)": ["tcp/ip", "dns", "networking"],
        "Google Cloud Platform (GCP)": ["gcp", "google cloud"],
        "Azure": ["azure"],
        "AI / Machine Learning Ops": ["mlops", "ai", "machine learning", "artificial intelligence"],
        "Chaos Engineering": ["chaos engineering"],
        "Toil Reduction / Automation": ["toil reduction", "automation"],
        "Capacity Planning": ["capacity planning"],
        "Performance Engineering": ["performance engineering", "performance tuning"],
        "Site Reliability Engineering": ["site reliability engineering", "sre"],
    }

    missing = []
    present = []
    for display_name, keywords in in_demand.items():
        found = any(kw in current_skills for kw in keywords)
        if found:
            present.append(display_name)
        else:
            missing.append(display_name)

    # Flag potentially outdated skills
    legacy_keywords = {"solaris", "websphere application server", "oracle application server",
                       "soa", "vmware infrastructure"}
    outdated = [s.get("Name", "") for s in skills if s.get("Name", "").lower() in legacy_keywords]

    return present, missing, outdated


def suggest_headline(profile, positions):
    """Generate optimized headline suggestions."""
    current = profile.get("Headline", "")
    recent_roles = [p.get("Title", "") for p in positions[:3]]
    recent_companies = [p.get("Company Name", "") for p in positions[:3] if p.get("Company Name")]

    suggestions = []
    suggestions.append(
        f"Senior Site Reliability Engineer | Ex-Pinterest | Cloud Infrastructure | "
        f"Platform Engineering | Angel Investor"
    )
    suggestions.append(
        f"SRE & Platform Engineer | Kubernetes, AWS, Python | "
        f"Ex-Pinterest, Ex-Salesforce | Angel Investor & Startup CTO"
    )
    suggestions.append(
        f"Staff SRE / Infrastructure Engineer | 20+ Years in Distributed Systems | "
        f"Ex-Pinterest | Agentic AI Builder"
    )
    return current, suggestions


def suggest_summary(profile, positions, skills):
    """Generate an optimized About/Summary section."""
    years = datetime.now().year - 1997  # started in 1997
    return f"""Site Reliability Engineer and platform builder with {years}+ years of experience designing, scaling, and operating distributed systems at companies like Pinterest, Salesforce, and Verizon.

At Pinterest, I led reliability initiatives for infrastructure serving hundreds of millions of users, focusing on availability, observability, and incident response. Prior to that, I co-founded ZapChain, a blockchain social platform, as CTO -- building the full technical stack from zero to launch.

My technical foundation spans cloud infrastructure (AWS), container orchestration, CI/CD pipelines, Python, and systems programming. I'm passionate about reducing toil through automation and building self-healing systems.

Currently exploring agentic AI systems and investing in early-stage startups as an angel investor.

Core expertise: Site Reliability Engineering, Cloud Infrastructure, Distributed Systems, Platform Engineering, Kubernetes, Python, AWS, Observability, Incident Management, Automation, Blockchain, Technical Leadership"""


def suggest_position_descriptions(positions):
    """Generate description suggestions for positions that lack them."""
    suggestions = {}

    templates = {
        "Pinterest": (
            "Site Reliability Engineer",
            """- Ensured high availability and reliability of Pinterest's core infrastructure serving 400M+ monthly users
- Designed and implemented monitoring, alerting, and observability solutions to reduce MTTR
- Led incident response and post-incident review processes to improve system resilience
- Automated operational toil through Python tooling and infrastructure-as-code
- Collaborated with product engineering teams on capacity planning and performance optimization
- Technologies: AWS, Kubernetes, Python, Terraform, Prometheus, Grafana"""
        ),
        "Salesforce": (
            "Software Consultant",
            """- Provided technical consulting for Salesforce platform infrastructure and integrations
- Designed and implemented scalable cloud-based solutions for enterprise clients
- Collaborated with cross-functional teams to deliver reliability improvements
- Technologies: Cloud Computing, Linux, Python, Integration Architecture"""
        ),
        "Verizon Enterprise Solutions Group": (
            "Sr. Technical Architect",
            """- Led technical architecture for enterprise solutions serving Fortune 500 clients
- Designed high-availability distributed systems and disaster recovery strategies
- Managed cross-team technical initiatives spanning data center and cloud infrastructure
- Mentored engineering teams on system design best practices
- Technologies: Linux, Solaris, VMware, Shell Scripting, Enterprise Architecture"""
        ),
        "IBM": (
            "Systems Engineer",
            """- Engineered and maintained enterprise server infrastructure for client environments
- Performed system administration, capacity planning, and performance tuning
- Supported migration projects and technology modernization initiatives
- Technologies: Linux, Unix, Shell Scripting"""
        ),
    }

    for pos in positions:
        company = pos.get("Company Name", "")
        desc = pos.get("Description", "").strip()
        if not desc and company in templates:
            title, suggested = templates[company]
            suggestions[f"{company} - {pos.get('Title', '')}"] = suggested

    return suggestions


def print_report(profile, summary, positions, skills, education, certs, endorsements, recs):
    """Print the full optimization report."""
    print("=" * 70)
    print("  LINKEDIN PROFILE OPTIMIZER")
    print("  Optimizing for AI Recruiting Systems (HiredScore / Workday)")
    print("=" * 70)

    # --- Completeness Score ---
    scores, max_points = analyze_completeness(
        profile, summary, positions, skills, education, certs, endorsements, recs
    )
    total = sum(v[0] for v in scores.values())
    pct = int(100 * total / max_points) if max_points else 0

    print(f"\n{'=' * 70}")
    print(f"  PROFILE COMPLETENESS SCORE: {total}/{max_points} ({pct}%)")
    print(f"{'=' * 70}\n")

    for field, (pts, note) in scores.items():
        bar_len = 20
        filled = int(bar_len * pts / max(1, {
            "Headline": 10, "Summary/About": 15, "Positions": 20,
            "Skills": 10, "Education": 5, "Certifications": 5,
            "Endorsements": 5, "Recommendations": 5, "Recent Activity": 5,
        }.get(field, 5)))
        bar = "#" * filled + "-" * (bar_len - filled)
        print(f"  {field:<20s} [{bar}] {pts}pts  {note}")

    # --- Skills Gap ---
    present, missing, outdated = analyze_skills_gap(skills)
    print(f"\n{'=' * 70}")
    print("  SKILLS ANALYSIS")
    print(f"{'=' * 70}\n")

    if present:
        print(f"  In-demand skills you HAVE ({len(present)}):")
        for s in present:
            print(f"    + {s}")

    if missing:
        print(f"\n  In-demand skills to ADD ({len(missing)}):")
        print("  (Add ones you actually have experience with)\n")
        for s in missing:
            print(f"    - {s}")

    if outdated:
        print(f"\n  Consider REMOVING or de-prioritizing:")
        for s in outdated:
            print(f"    x {s}")
        print("    (These signal legacy experience to AI matchers)")

    # --- Headline ---
    current_headline, suggestions = suggest_headline(profile, positions)
    print(f"\n{'=' * 70}")
    print("  HEADLINE OPTIMIZATION")
    print(f"{'=' * 70}\n")
    print(f"  Current:  {current_headline}")
    print(f"  ({len(current_headline)} chars)\n")
    print("  Suggested alternatives:\n")
    for i, s in enumerate(suggestions, 1):
        print(f"  {i}. {s}")
        print(f"     ({len(s)} chars)\n")

    # --- Summary ---
    print(f"{'=' * 70}")
    print("  SUGGESTED ABOUT/SUMMARY")
    print(f"{'=' * 70}\n")
    suggested_summary = suggest_summary(profile, positions, skills)
    for line in suggested_summary.split("\n"):
        print(f"  {line}")

    # --- Position Descriptions ---
    pos_suggestions = suggest_position_descriptions(positions)
    if pos_suggestions:
        print(f"\n{'=' * 70}")
        print("  SUGGESTED POSITION DESCRIPTIONS")
        print(f"{'=' * 70}")
        for role, desc in pos_suggestions.items():
            print(f"\n  >> {role}\n")
            for line in desc.split("\n"):
                print(f"  {line}")

    # --- Quick Wins ---
    print(f"\n{'=' * 70}")
    print("  QUICK WINS (highest impact, lowest effort)")
    print(f"{'=' * 70}\n")

    wins = []
    if not summary.strip():
        wins.append(("Add About/Summary", "CRITICAL",
                      "Copy the suggested summary above into your LinkedIn About section"))
    if len(profile.get("Headline", "")) < 60:
        wins.append(("Expand Headline", "HIGH",
                      "Replace with one of the keyword-rich suggestions above"))
    blank_positions = sum(1 for p in positions if not p.get("Description", "").strip())
    if blank_positions > 0:
        wins.append((f"Add {blank_positions} Position Descriptions", "HIGH",
                      "Especially Pinterest and Verizon - your longest tenures"))
    if len(skills) < 50:
        wins.append((f"Add {50 - len(skills)} More Skills", "MEDIUM",
                      "Fill up to the 50-skill maximum with in-demand skills you have"))
    if len(recs) < 3:
        wins.append(("Get More Recommendations", "MEDIUM",
                      "Ask 3-5 former colleagues, especially from Pinterest"))
    if len(certs) < 3:
        wins.append(("Add Certifications", "MEDIUM",
                      "AWS, Kubernetes (CKA), or Terraform certs are high-signal"))

    # Check for typo in education
    for edu in education:
        school = edu.get("School Name", "")
        if "Technologoy" in school:
            wins.append(("Fix Education Typo", "LOW",
                          f"'{school}' has a typo - should be 'Technology'"))

    for title, priority, action in wins:
        print(f"  [{priority:>8s}]  {title}")
        print(f"             {action}\n")

    print(f"{'=' * 70}")
    print(f"  Estimated score after all fixes: ~85-90% (from {pct}%)")
    print(f"{'=' * 70}\n")


def main():
    profile = load_profile()
    summary = load_summary()
    positions = load_positions()
    skills = load_skills()
    education = load_education()
    certs = load_certifications()
    endorsements = load_endorsements()
    recs = load_recommendations()

    print_report(profile, summary, positions, skills, education, certs, endorsements, recs)


if __name__ == "__main__":
    main()
