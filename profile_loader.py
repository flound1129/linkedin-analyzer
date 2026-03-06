"""Parse LinkedIn CSV export and resume PDFs into structured profile data."""

import csv
from pathlib import Path

import pdfplumber

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



def load_profile(data_dir=None):
    """Load all LinkedIn export CSVs into a single structured dict."""
    profile_rows = _read_csv("Profile.csv", data_dir)
    p = profile_rows[0] if profile_rows else {}

    summary_rows = _read_csv("Profile Summary.csv", data_dir)
    summary = ""
    if summary_rows:
        summary = summary_rows[0].get("Profile Summary", "")
    if not summary:
        summary = p.get("Summary", "")

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

    skills = []
    for row in _read_csv("Skills.csv", data_dir):
        name = row.get("Name", "").strip()
        if name:
            skills.append(name)

    education = []
    for row in _read_csv("Education.csv", data_dir):
        education.append({
            "school": row.get("School Name", ""),
            "degree": row.get("Degree Name", ""),
            "start_date": row.get("Start Date", ""),
            "end_date": row.get("End Date", ""),
            "activities": row.get("Activities", ""),
        })

    certifications = []
    for row in _read_csv("Certifications.csv", data_dir):
        certifications.append({
            "name": row.get("Name", ""),
            "authority": row.get("Authority", ""),
            "license_number": row.get("License Number", ""),
        })

    endorsements = []
    for row in _read_csv("Endorsement_Received_Info.csv", data_dir):
        endorsements.append({
            "skill": row.get("Skill Name", ""),
            "endorser": f"{row.get('Endorser First Name', '')} {row.get('Endorser Last Name', '')}".strip(),
            "date": row.get("Endorsement Date", ""),
        })

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


def load_resume_pdf(pdf_path):
    """Extract text from a resume PDF file."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume PDF not found: {pdf_path}")

    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)

    return "\n\n".join(pages)


def resume_to_text(pdf_path):
    """Load a resume PDF and return formatted text for Claude prompts."""
    raw_text = load_resume_pdf(pdf_path)
    return f"Resume (from PDF):\n\n{raw_text}"
