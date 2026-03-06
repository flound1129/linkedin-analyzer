#!/usr/bin/env python3
"""HiredScore Optimizer — Simulate AI recruiting scores, detect bias, get advice."""

import argparse
import json
import os
import sys
from pathlib import Path

import anthropic

from profile_loader import load_profile, profile_to_text, resume_to_text
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
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
    return json.loads(text)


def get_profile_text(args):
    """Get profile text from either a resume PDF or LinkedIn data export."""
    if getattr(args, "resume", None):
        return resume_to_text(args.resume)
    profile = load_profile(args.data_dir)
    return profile_to_text(profile)


def cmd_score(args):
    client = get_client()
    profile_text = get_profile_text(args)

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
    client = get_client()
    profile_text = get_profile_text(args)

    system_prompt = build_audit_system_prompt()
    user_message = build_audit_user_message(profile_text)

    print("\nRunning bias audit...\n")

    result = call_claude(client, system_prompt, user_message)
    print_bias_audit(result)


def cmd_advise(args):
    client = get_client()
    profile_text = get_profile_text(args)

    system_prompt = build_advisor_system_prompt(profile_text)

    if getattr(args, "resume", None):
        name = Path(args.resume).stem
        headline = "Resume PDF"
    else:
        profile = load_profile(args.data_dir)
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
  %(prog)s score                              Score LinkedIn profile
  %(prog)s score --resume resume.pdf          Score a resume PDF
  %(prog)s score --resume r.pdf --job-file j  Score resume against job description
  %(prog)s audit                              Detect bias signals (LinkedIn)
  %(prog)s audit --resume resume.pdf          Detect bias signals (PDF)
  %(prog)s advise                             Interactive advisor
        """,
    )
    parser.add_argument("--data-dir", default=None, help="Path to LinkedIn data export directory")

    subparsers = parser.add_subparsers(dest="command")

    score_parser = subparsers.add_parser("score", help="Simulate HiredScore grading")
    score_parser.add_argument("--job-file", help="Path to job description file")
    score_parser.add_argument("--job", help="Job description text")
    score_parser.add_argument("--resume", help="Path to resume PDF file")
    score_parser.add_argument("--data-dir", default=None)

    audit_parser = subparsers.add_parser("audit", help="Detect bias-prone signals")
    audit_parser.add_argument("--resume", help="Path to resume PDF file")
    audit_parser.add_argument("--data-dir", default=None)

    advise_parser = subparsers.add_parser("advise", help="Interactive advisor")
    advise_parser.add_argument("--resume", help="Path to resume PDF file")
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
