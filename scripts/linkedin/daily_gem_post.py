"""
Daily Hidden Gem LinkedIn post for Daanaa.

Workflow:
  1. Pick a hidden gem from the DB (never-featured, has mission + website)
  2. Search LinkedIn for their company page (via linkedin-api)
  3. Generate a warm, specific post using qwen2.5:7b (fast — short post)
  4. Post to the Daanaa LinkedIn page, tagging the org if found
  5. Record the EIN in .featured_gems.json to avoid repeats

Usage:
  python3 daily_gem_post.py                    # pick, generate, post
  python3 daily_gem_post.py --dry-run          # print post without posting
  python3 daily_gem_post.py --ein 202910382    # force a specific org
  python3 daily_gem_post.py --no-llm          # use template (layout/speed test)
"""
import argparse
import json
import re
import sqlite3
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
DB_PATH = BASE.parent.parent / "data" / "merit_registry.db"
FEATURED_LOG = BASE / ".featured_gems.json"
LINKEDIN_INDEX = BASE / ".gem_linkedin_index.json"
SESSION_FILE = BASE / ".session" / "state.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"   # short post — no need for 30b

NTEE_LABELS = {
    "A": "Arts & Culture", "B": "Education", "C": "Environment",
    "D": "Animal Services", "E": "Health", "F": "Mental Health",
    "G": "Diseases & Disorders", "H": "Medical Research", "I": "Crime & Legal",
    "J": "Employment", "K": "Food & Agriculture", "L": "Housing",
    "M": "Public Safety", "N": "Recreation & Sports", "O": "Youth Development",
    "P": "Social Services", "Q": "International", "R": "Civil Rights",
    "S": "Community Development", "T": "Philanthropy", "U": "Science",
    "V": "Social Science", "W": "Public Affairs", "X": "Religion",
    "Y": "Mutual Aid", "Z": "Unknown",
}


# ---------------------------------------------------------------------------
# Featured gem log
# ---------------------------------------------------------------------------
def load_featured() -> set:
    if FEATURED_LOG.exists():
        return set(json.loads(FEATURED_LOG.read_text()))
    return set()


def mark_featured(ein: str):
    featured = load_featured()
    featured.add(ein)
    FEATURED_LOG.write_text(json.dumps(sorted(featured), indent=2))


# ---------------------------------------------------------------------------
# Org selection
# ---------------------------------------------------------------------------
def _load_linkedin_index() -> dict:
    if LINKEDIN_INDEX.exists():
        return json.loads(LINKEDIN_INDEX.read_text())
    return {}


def pick_gem(ein: str = None, slot: int = 0) -> dict:
    """
    Pick a hidden gem. slot=0 → highest followers, slot=1 → second highest.
    Falls back to random if LinkedIn index is sparse.
    """
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    if ein:
        row = db.execute("""
            SELECT EIN, organization_name, CITY, STATE, NTEE1, mission,
                   website, merit_score, merit_health_signal_v5,
                   merit_band_v5_label, peer_percentile, total_revenue,
                   ruling_date, cause_tags
            FROM registry_enriched WHERE EIN = ?
        """, (ein,)).fetchone()
        db.close()
        return dict(row) if row else None

    featured = load_featured()
    li_index = _load_linkedin_index()

    # Build ranked candidate list from LinkedIn index (found pages, not featured yet)
    ranked = sorted(
        [
            (v["followers"], ein)
            for ein, v in li_index.items()
            if v.get("found") and ein not in featured
        ],
        reverse=True,
    )

    # Pick by slot (0 = top, 1 = second)
    if len(ranked) > slot:
        target_ein = ranked[slot][1]
        row = db.execute("""
            SELECT EIN, organization_name, CITY, STATE, NTEE1, mission,
                   website, merit_score, merit_health_signal_v5,
                   merit_band_v5_label, peer_percentile, total_revenue,
                   ruling_date, cause_tags
            FROM registry_enriched WHERE EIN = ? AND org_status = 'active'
        """, (target_ein,)).fetchone()
        if row:
            db.close()
            return dict(row)

    # Fallback: random from DB (index not yet populated)
    featured_list = list(featured) if featured else [""]
    placeholders = ",".join("?" * len(featured_list))
    row = db.execute(f"""
        SELECT EIN, organization_name, CITY, STATE, NTEE1, mission,
               website, merit_score, merit_health_signal_v5,
               merit_band_v5_label, peer_percentile, total_revenue,
               ruling_date, cause_tags
        FROM registry_enriched
        WHERE is_hidden_gem = 1
          AND org_status = 'active'
          AND mission IS NOT NULL
          AND website IS NOT NULL
          AND merit_health_signal_v5 = 'HEALTHY'
          AND EIN NOT IN ({placeholders})
        ORDER BY peer_percentile DESC
        LIMIT {slot + 1}
    """, featured_list).fetchall()
    db.close()
    return dict(row[slot]) if row and len(row) > slot else None


# ---------------------------------------------------------------------------
# LinkedIn company search
# ---------------------------------------------------------------------------
def find_linkedin_page(org_name: str, ein: str = None) -> dict | None:
    """Return {name, url, followers} if confident match found, else None.
    Checks enrichment index first to avoid live API calls."""
    if ein:
        index = _load_linkedin_index()
        if ein in index and index[ein].get("found"):
            entry = index[ein]
            return {"name": entry["name"], "url": entry["url"], "followers": entry["followers"]}

    creds_file = BASE / ".session" / "linkedin_creds.json"
    if not creds_file.exists():
        return None
    try:
        from linkedin_api import Linkedin
        creds = json.loads(creds_file.read_text())
        client = Linkedin(creds["username"], creds["pass"])
        results = client.search_companies(keywords=[org_name], limit=3)
        if not results:
            return None
        top = results[0]
        top_name = top.get("name", "").lower()
        query_words = set(w for w in org_name.lower().split() if len(w) > 3)
        overlap = query_words & set(top_name.split())
        if not overlap and len(query_words) > 1:
            return None
        urn_id = top.get("urn_id", "")
        followers = int(re.search(r'([\d,]+)\s+follower', top.get("subline") or "", re.I).group(1).replace(",", "")) \
            if re.search(r'([\d,]+)\s+follower', top.get("subline") or "", re.I) else 0
        return {
            "name": top.get("name", ""),
            "url": f"https://www.linkedin.com/company/{urn_id}/" if urn_id else None,
            "followers": followers,
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Content generation
# ---------------------------------------------------------------------------
NTEE_CAUSE_MAP = {
    "A": "arts and culture", "B": "education", "C": "environmental work",
    "D": "animal welfare", "E": "health care", "F": "mental health",
    "G": "disease research", "H": "medical research", "I": "legal aid",
    "J": "job training", "K": "food access", "L": "affordable housing",
    "M": "public safety", "N": "recreation", "O": "youth programs",
    "P": "social services", "Q": "international aid", "R": "civil rights",
    "S": "community development", "T": "charitable giving", "U": "science",
    "V": "social research", "W": "civic affairs", "X": "faith communities",
    "Y": "member services", "Z": "general community work",
}


def generate_post(org: dict, linkedin_page: dict | None, no_llm: bool = False) -> str:
    name = org["organization_name"].title()
    city = org["CITY"].title()
    state = org["STATE"]
    cause = NTEE_CAUSE_MAP.get(org["NTEE1"], "community work")
    mission = org["mission"]
    score = org["peer_percentile"]
    band = org["merit_band_v5_label"] or ""
    revenue = org["total_revenue"] or 0
    li_url = linkedin_page["url"] if linkedin_page else None

    daanaa_url = f"https://daanaa.org/org/{org['EIN']}"
    location_str = f"{city}, {state}"
    revenue_str = (
        f"${revenue/1e6:.1f}M" if revenue >= 1e6
        else f"${revenue/1e3:.0f}K" if revenue >= 1e3
        else f"${int(revenue)}"
    )

    if no_llm:
        tag_line = f"\n\nFind them on LinkedIn: {li_url}" if li_url else ""
        return (
            f"Today's hidden gem: {name} in {location_str}.\n\n"
            f"{mission}\n\n"
            f"They're in the top {100 - int(score)}% of {cause} organizations "
            f"in the {band} category — operating on {revenue_str} a year.\n\n"
            f"More on Daanaa: {daanaa_url}"
            f"{tag_line}\n\n"
            f"#nonprofit #hiddenGem #{cause.replace(' ', '').title()}"
        )

    prompt = f"""You write warm, specific LinkedIn posts for Daanaa — a nonprofit discovery platform.

Write a short LinkedIn post (under 200 words) featuring this hidden gem nonprofit.

Org: {name}
Location: {location_str}
What they do: {mission}
Cause area: {cause}
Annual revenue: {revenue_str}
Financial context: Top {100 - int(score):.0f}% of peers in the {band} size band

Rules:
- Opening line must be specific and human, not generic ("Today's hidden gem" is fine as a format but avoid clichés)
- Name the city and what they do in plain language
- Include ONE specific detail (their size, their peer standing, or something implied by their mission)
- End with an invite to learn more at: {daanaa_url}
{'- Last line: "Find them on LinkedIn: ' + li_url + '"' if li_url else ''}
- Add 3–4 hashtags: always #nonprofit, then 2–3 specific to their cause/location
- No em dashes. No hyphenated jargon. Kitchen-table language only.
- Do NOT mention Daanaa's scoring methodology or numbers — just "strong financial health for their size"

Return ONLY the post text, no explanation."""

    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.8, "num_predict": 400},
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    print(f"  Generating post with {MODEL}...")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["response"].strip()


# ---------------------------------------------------------------------------
# LinkedIn post
# ---------------------------------------------------------------------------
def post_to_linkedin(text: str, company_id: str = "133385169"):
    import sys
    sys.path.insert(0, str(BASE))
    import linkedin_poster as poster
    poster.post_text(text, company_id)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Daanaa daily hidden gem LinkedIn post")
    parser.add_argument("--ein", help="Feature a specific EIN")
    parser.add_argument("--slot", type=int, default=0,
                        help="0 = top gem (morning), 1 = second gem (afternoon)")
    parser.add_argument("--dry-run", action="store_true", help="Print post, don't publish")
    parser.add_argument("--no-llm", action="store_true", help="Use template (skip LLM)")
    parser.add_argument("--company-id", default="133385169")
    args = parser.parse_args()

    # 1. Pick org
    org = pick_gem(args.ein, slot=args.slot)
    if not org:
        print("No unfeatured hidden gems available. Reset .featured_gems.json to restart.")
        return

    name = org["organization_name"].title()
    print(f"\nToday's gem: {name} ({org['EIN']}) — {org['CITY'].title()}, {org['STATE']}")
    print(f"  Sector: {NTEE_LABELS.get(org['NTEE1'], 'Unknown')}")
    print(f"  Health: {org['merit_health_signal_v5']} | Peer %ile: {org['peer_percentile']:.0f}")

    # 2. Find LinkedIn page (index first, live search as fallback)
    print(f"  Looking up LinkedIn page...")
    li_page = find_linkedin_page(org["organization_name"], ein=org["EIN"])
    if li_page:
        print(f"  LinkedIn: {li_page['name']} → {li_page['url']}")
    else:
        print("  LinkedIn: no confident match found — posting without tag")

    # 3. Generate post
    post_text = generate_post(org, li_page, no_llm=args.no_llm)

    print("\n" + "─" * 60)
    print(post_text)
    print("─" * 60)

    if args.dry_run:
        print("\nDry run — not posted. Use without --dry-run to publish.")
        return

    # 4. Post
    if not SESSION_FILE.exists():
        print("\nNo LinkedIn session. Run linkedin_poster.py --setup first.")
        return

    print("\nPosting to LinkedIn...")
    post_to_linkedin(post_text, args.company_id)

    # 5. Record
    mark_featured(org["EIN"])
    print(f"Done. {name} marked as featured.")


if __name__ == "__main__":
    main()
