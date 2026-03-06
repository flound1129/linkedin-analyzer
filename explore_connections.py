#!/usr/bin/env python3
"""Explore LinkedIn connections data from CSV export."""

import csv
import sys
from collections import Counter
from pathlib import Path

CSV_PATH = Path(__file__).parent / "linkedin_data" / "Connections.csv"


def load_connections():
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        # Skip the notes header lines before the actual CSV
        for line in f:
            if line.startswith("First Name,"):
                break
        reader = csv.DictReader(f, fieldnames=["First Name", "Last Name", "URL", "Email Address", "Company", "Position", "Connected On"])
        for row in reader:
            rows.append(row)
    return rows


def top_companies(connections, n=20):
    companies = Counter(c["Company"].strip() for c in connections if c["Company"].strip())
    print(f"\nTop {n} Companies in Your Network:")
    print("-" * 50)
    for company, count in companies.most_common(n):
        print(f"  {count:>3}  {company}")


def top_positions(connections, n=20):
    positions = Counter(c["Position"].strip() for c in connections if c["Position"].strip())
    print(f"\nTop {n} Positions in Your Network:")
    print("-" * 50)
    for position, count in positions.most_common(n):
        print(f"  {count:>3}  {position}")


def search(connections, query):
    query = query.lower()
    results = []
    for c in connections:
        searchable = f"{c['First Name']} {c['Last Name']} {c['Company']} {c['Position']}".lower()
        if query in searchable:
            results.append(c)
    print(f"\nSearch results for '{query}' ({len(results)} found):")
    print("-" * 50)
    for c in results:
        email = f" <{c['Email Address']}>" if c["Email Address"].strip() else ""
        print(f"  {c['First Name']} {c['Last Name']}{email}")
        print(f"    {c['Position']} @ {c['Company']}")
        print(f"    {c['URL']}")
        print()


def with_emails(connections):
    results = [c for c in connections if c["Email Address"].strip()]
    print(f"\nConnections with email addresses ({len(results)}):")
    print("-" * 50)
    for c in results:
        print(f"  {c['First Name']} {c['Last Name']} <{c['Email Address']}>")
        print(f"    {c['Position']} @ {c['Company']}")
        print()


def summary(connections):
    companies = Counter(c["Company"].strip() for c in connections if c["Company"].strip())
    with_email = sum(1 for c in connections if c["Email Address"].strip())
    print(f"\nNetwork Summary:")
    print("-" * 50)
    print(f"  Total connections: {len(connections)}")
    print(f"  Unique companies:  {len(companies)}")
    print(f"  With email:        {with_email}")


def main():
    connections = load_connections()

    if len(sys.argv) < 2:
        print("Usage: python explore_connections.py <command> [args]")
        print()
        print("Commands:")
        print("  summary              Overview of your network")
        print("  companies [n]        Top N companies (default 20)")
        print("  positions [n]        Top N positions (default 20)")
        print("  search <query>       Search by name, company, or position")
        print("  emails               List connections with email addresses")
        return

    cmd = sys.argv[1].lower()

    if cmd == "summary":
        summary(connections)
    elif cmd == "companies":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        top_companies(connections, n)
    elif cmd == "positions":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        top_positions(connections, n)
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: python explore_connections.py search <query>")
            return
        search(connections, " ".join(sys.argv[2:]))
    elif cmd == "emails":
        with_emails(connections)
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
