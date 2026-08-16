#!/usr/bin/env python3
"""
T12 Phase 2: Test typo tolerance implementation against a test set of queries.

Measures recall@5 (how many of the expected matches appear in top 5 results).

Usage:
    python3 scripts/test_typo_tolerance.py [--api http://localhost:5000]
"""

import requests
import argparse
from typing import Tuple

# Test set: (query, expected_org_name_substring, category, notes)
TEST_SET = [
    ("food bank", "Food", "Hunger", "Exact nominal"),
    ("fod bank", "Food", "Hunger", "Missing 'o'"),
    ("enviromental", "Environmental", "Environment", "Missing 'n'"),
    ("womens shelter", "Women", "Women", "Possessive"),
    ("homeless shelter", "Homelessness", "Homelessness", "Word order"),
    ("childrens hospital", "Children", "Healthcare", "Possessive"),
    ("mental helth", "Mental", "Mental Health", "Misspelled 'health'"),
    ("aniaml rescue", "Animal", "Animals", "Misspelled 'animal'"),
    ("cancer reserch", "Cancer", "Cancer", "Misspelled 'research'"),
    ("diabetes assoc", "Diabetes", "Diabetes", "Abbreviation"),
    ("heart assn", "Heart", "Cardiovascular", "Abbreviation"),
    ("red cross", "Red Cross", "Disaster", "Nominal"),
    ("salvation army", "Salvation", "Social Services", "Nominal"),
    ("goodwill", "Goodwill", "Job Training", "Nominal"),
    ("planned parenthood", "Planned", "Reproductive Health", "Nominal"),
    ("sierra club", "Sierra", "Conservation", "Nominal"),
    ("greenpeace", "Greenpeace", "Environmental", "Nominal"),
    ("amnisty international", "Amnesty", "Human Rights", "Misspelled"),
    ("doctors without borders", "Médecins", "International", "English nominal"),
    ("oxfam", "Oxfam", "International Relief", "Nominal"),
    ("wwf", "Wildlife", "Wildlife", "Abbreviation"),
    ("unicef", "UNICEF", "International", "Nominal"),
    ("urban league", "Urban", "Civil Rights", "Nominal"),
    ("naacp", "NAACP", "Civil Rights", "Abbreviation"),
    ("aclu", "ACLU", "Civil Rights", "Abbreviation"),
    ("habitat for humanity", "Habitat", "Housing", "Nominal"),
    ("habitat for humanty", "Habitat", "Housing", "Misspelled"),
    ("st judes", "Jude", "Pediatric Cancer", "Apostrophe variation"),
    ("boys and girls club", "Boys", "Youth", "Ampersand variation"),
    ("boys & girls club", "Boys", "Youth", "Ampersand form"),
    ("special olympics", "Special Olympics", "Disability Sports", "Nominal"),
    ("ds", "Down", "Disability", "Abbreviation"),
    ("autism speaks", "Autism", "Autism", "Nominal"),
    ("cerebral palsy assoc", "Cerebral", "Disability", "Abbreviated"),
    ("muscular distrophy", "Muscular", "Disability", "Misspelled"),
    ("leukemia lymphoma", "Leukemia", "Blood Cancer", "Abbreviated"),
    ("nature consrvancy", "Nature", "Conservation", "Misspelled"),
    ("national parks", "Parks", "Conservation", "Partial name"),
    ("world animal foundation", "Animal", "Animals", "Nominal"),
    ("peta", "PETA", "Animal Rights", "Abbreviation"),
    ("humane society", "Humane", "Animals", "Nominal"),
    ("aspca", "ASPCA", "Animal Welfare", "Abbreviation"),
    ("meals on wheels", "Meals", "Senior Services", "Nominal"),
    ("meals on wheels america", "Meals", "Senior Services", "Full nominal"),
    ("boys town", "Boys", "Youth", "Nominal"),
    ("kiva", "Kiva", "Microfinance", "Nominal"),
    ("khan academy", "Khan", "Education", "Nominal"),
    ("khan acedemy", "Khan", "Education", "Misspelled"),
    ("city year", "City", "Youth", "Nominal"),
    ("teach for america", "Teach", "Education", "Nominal"),
]

def test_query(api_url: str, query: str, expected_substring: str) -> Tuple[bool, int]:
    """
    Test a single query against the API.
    Returns (found, position) where:
    - found: True if expected_substring appears in top 5 results
    - position: rank (1-5) if found, -1 if not found in top 5
    """
    try:
        resp = requests.get(
            f"{api_url}/api/search",
            params={"q": query},
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])

        for rank, org in enumerate(results[:5], 1):
            org_name = org.get("organization_name", "").lower()
            if expected_substring.lower() in org_name:
                return True, rank

        return False, -1
    except Exception as e:
        print(f"  ERROR testing '{query}': {e}")
        return False, -1

def main():
    parser = argparse.ArgumentParser(description="Test typo tolerance implementation")
    parser.add_argument("--api", default="http://localhost:5000", help="API base URL")
    args = parser.parse_args()

    print("=" * 80)
    print("T12 PHASE 2: TYPO TOLERANCE RECALL TEST")
    print("=" * 80)
    print(f"API: {args.api}")
    print(f"Test set: {len(TEST_SET)} queries")
    print()

    found = 0
    results_by_rank = {i: 0 for i in range(1, 6)}

    for i, (query, expected, category, notes) in enumerate(TEST_SET, 1):
        success, rank = test_query(args.api, query, expected)
        if success:
            found += 1
            results_by_rank[rank] += 1
            status = f"✓ rank {rank}"
        else:
            status = "✗"

        print(f"{i:2}. {status:12} | '{query:30}' → {expected[:30]:30} ({category})")

    recall = found / len(TEST_SET) * 100
    print()
    print("=" * 80)
    print(f"RECALL@5: {recall:.1f}% ({found}/{len(TEST_SET)})")
    print()
    print("Distribution by rank:")
    for rank in range(1, 6):
        pct = results_by_rank[rank] / found * 100 if found > 0 else 0
        print(f"  Rank {rank}: {results_by_rank[rank]:2} ({pct:5.1f}%)")
    print()
    print("DECISION GATE: Recall > 90% → Ship Phase 2")
    if recall > 90:
        print("✓ GATE PASSED — Ready for deployment")
    else:
        print("✗ GATE FAILED — Iterate on typo tolerance parameters")
    print("=" * 80)

if __name__ == "__main__":
    main()
