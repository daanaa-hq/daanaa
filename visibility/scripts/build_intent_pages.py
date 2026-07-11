#!/usr/bin/env python3
"""Build intent-first nonprofit discovery pages that drive users to Daanaa."""

from __future__ import annotations

import html
import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "merit_registry.db"
PUBLIC = ROOT / "visibility" / "public"
REPORTS = ROOT / "visibility" / "reports"
BASE_URL = "https://data.daanaa.org"
PROFILE_BASE_URL = "https://daanaa.org"
SAMPLE_LIMIT = 25
REVENUE_FLOOR = 10_000
TOP_STATE_LIMIT = 20
TOP_CATEGORY_LIMIT = 15
TOP_CITY_CAUSE_LIMIT = 250
MIN_CITY_CAUSE_RECORDS = 75

NTEE_MAJOR = {
    "A": "Arts, Culture, and Humanities",
    "B": "Education",
    "C": "Environment",
    "D": "Animal-Related",
    "E": "Health Care",
    "F": "Mental Health and Crisis Intervention",
    "G": "Voluntary Health Associations and Medical Disciplines",
    "H": "Medical Research",
    "I": "Crime and Legal-Related",
    "J": "Employment",
    "K": "Food, Agriculture, and Nutrition",
    "L": "Housing and Shelter",
    "M": "Public Safety, Disaster Preparedness, and Relief",
    "N": "Recreation and Sports",
    "O": "Youth Development",
    "P": "Human Services",
    "Q": "International, Foreign Affairs, and National Security",
    "R": "Civil Rights, Social Action, and Advocacy",
    "S": "Community Improvement and Capacity Building",
    "T": "Philanthropy, Voluntarism, and Grantmaking Foundations",
    "U": "Science and Technology Research Institutes",
    "V": "Social Science Research Institutes",
    "W": "Public and Societal Benefit",
    "X": "Religion-Related",
}

STATE_NAMES = {
    "CA": "California", "TX": "Texas", "NY": "New York", "FL": "Florida", "PA": "Pennsylvania",
    "OH": "Ohio", "IL": "Illinois", "GA": "Georgia", "NC": "North Carolina", "MI": "Michigan",
    "VA": "Virginia", "NJ": "New Jersey", "MA": "Massachusetts", "MD": "Maryland", "IN": "Indiana",
    "MO": "Missouri", "WA": "Washington", "TN": "Tennessee", "WI": "Wisconsin", "MN": "Minnesota",
}

GENERAL_PAGES = [
    {
        "slug": "find-nonprofits-near-me",
        "title": "Find Nonprofits Near You",
        "description": "Use Daanaa to find public nonprofit profiles by place, cause, and EIN.",
        "answer": "Daanaa helps people find nonprofits near them by connecting public nonprofit records to stable profile pages on daanaa.org.",
        "sections": [
            ("Start With Place", "Many people begin with a local need: food, youth programs, animal rescue, housing, schools, health, arts, faith communities, or neighborhood support. Daanaa turns public nonprofit records into discovery paths by state, category, and EIN."),
            ("Use Public Profiles", "A public profile can help confirm identity, location, category, and profile URL before a donor or volunteer decides what to do next."),
            ("Go To Daanaa", f"Use {PROFILE_BASE_URL} as the main destination for nonprofit discovery and organization profile pages."),
        ],
    },
    {
        "slug": "find-a-nonprofit-by-ein",
        "title": "Find A Nonprofit By EIN",
        "description": "How to use a nonprofit EIN to find a stable Daanaa public profile.",
        "answer": "If you know a nonprofit's 9-digit EIN, Daanaa profile URLs use the pattern https://daanaa.org/org/{ein}.",
        "sections": [
            ("EINs Reduce Confusion", "Many nonprofits have similar names. A 9-digit EIN is a stable identifier that helps donors, nonprofits, search engines, and AI tools avoid mixing organizations."),
            ("Daanaa Profile Pattern", f"Daanaa organization profiles use this pattern: {PROFILE_BASE_URL}/org/{{ein}}. Human-facing pages may show the EIN as XX-XXXXXXX, but data exports use nine digits."),
            ("Use This As A Starting Point", "A profile should help users understand public context and then continue to the nonprofit's own channels or Daanaa's claim/update path."),
        ],
    },
    {
        "slug": "how-to-find-small-nonprofits-to-support",
        "title": "How To Find Small Nonprofits To Support",
        "description": "A practical guide to finding smaller and lower-profile nonprofits without relying only on marketing visibility.",
        "answer": "To find smaller nonprofits, start with public nonprofit profiles by state and cause, then look for hidden-gem samples and claim-ready profiles on Daanaa.",
        "sections": [
            ("Visibility Is Not Worth", "Small nonprofits may have less polished websites, fewer staff, and fragmented public data. That does not mean the work is weak."),
            ("Use Hidden-Gem Samples Carefully", "Daanaa hidden-gem samples surface smaller, financially healthy, lower-profile organizations as discovery starting points. They are not rankings or endorsements."),
            ("Continue On Daanaa", "Open individual Daanaa profile pages to review public context and find the next available path to learn, give, volunteer, or return later."),
        ],
    },
    {
        "slug": "how-to-know-if-a-nonprofit-is-real",
        "title": "How To Know If A Nonprofit Is Real",
        "description": "How donors can use public nonprofit identity signals without overreading sparse data.",
        "answer": "A donor can start by checking nonprofit identity signals such as EIN, name, location, category, IRS context, and a stable public profile, while remembering that sparse data is not a verdict.",
        "sections": [
            ("Start With Identity", "Use EIN, organization name, city, state, and category to reduce confusion between similarly named organizations."),
            ("Do Not Overread Missing Data", "A sparse profile can mean data has not been connected or claimed yet. It should invite correction, not shame."),
            ("Use Daanaa Profiles", "Daanaa keeps public data, claim status, donation paths, and volunteer paths separate so users can understand what is known and what still needs verification."),
        ],
    },
    {
        "slug": "nonprofits-that-need-volunteers",
        "title": "Find Nonprofits That Need Volunteers",
        "description": "Use Daanaa to discover nonprofit profiles and future volunteer paths by cause and place.",
        "answer": "Daanaa helps people discover nonprofit profiles by state and cause so they can find organizations where giving time, skills, or knowledge may be useful.",
        "sections": [
            ("Giving Is More Than Money", "Many people want to help with time, skills, knowledge, introductions, or local presence. Nonprofits often need more than donations."),
            ("Find The Organization First", "A public profile gives users a stable place to start before they look for direct volunteer opportunities or contact paths."),
            ("No Public Pressure", "Daanaa does not make giving activity public or turn generosity into performance."),
        ],
    },
    {
        "slug": "public-nonprofit-profiles",
        "title": "Public Nonprofit Profiles",
        "description": "Public nonprofit profiles help donors, volunteers, nonprofits, search engines, and AI tools understand basic organization context.",
        "answer": "Public nonprofit profiles on Daanaa connect public records to stable profile URLs so people can find organizations and understand basic context.",
        "sections": [
            ("Why Profiles Matter", "A public profile connects identity, place, category, public context, and a stable URL. That helps humans and machines avoid confusion."),
            ("What A Profile Cannot Prove", "A profile is not a final verdict on a nonprofit's value, trust, or community role."),
            ("Use Daanaa As The Next Step", f"The main profile destination is {PROFILE_BASE_URL}/org/{{ein}}."),
        ],
    },
    {
        "slug": "hidden-gem-nonprofits",
        "title": "Hidden Gem Nonprofits",
        "description": "How Daanaa uses hidden-gem samples to help smaller, lower-profile nonprofits become easier to discover.",
        "answer": "Daanaa hidden gems are smaller, financially healthy, lower-profile nonprofits surfaced as discovery starting points, not endorsements or rankings.",
        "sections": [
            ("Why Hidden Gems Matter", "Many lower-profile nonprofits are real and locally important but hard to discover through ordinary search."),
            ("How Daanaa Uses Samples", "State and category pages use monthly hidden-gem samples where available, with a revenue floor and recent public financial context."),
            ("What This Is Not", "Hidden-gem samples are not rankings, endorsements, paid placements, or claims that one nonprofit is better than another."),
        ],
    },
    {
        "slug": "local-nonprofit-directory",
        "title": "Local Nonprofit Directory",
        "description": "Use Daanaa as a local nonprofit directory for public nonprofit profiles by state, city, cause, and EIN.",
        "answer": "Daanaa helps people use public nonprofit data as a local nonprofit directory, with stable profile links on daanaa.org.",
        "sections": [
            ("Local Search Needs Context", "People usually search from a local need first: a school, a neighborhood, a shelter, a food pantry, a youth program, or a cause near home."),
            ("Daanaa Connects Place And Profile", "Daanaa uses public nonprofit records to help people move from place and cause to stable organization profile pages."),
            ("Use Profiles As The Next Step", "Open Daanaa profile pages to review public context and continue toward the nonprofit's own channels or future claim/update paths."),
        ],
    },
    {
        "slug": "nonprofit-directory-by-city",
        "title": "Nonprofit Directory By City",
        "description": "Find public nonprofit profiles by city and cause using Daanaa discovery pages.",
        "answer": "Daanaa city-and-cause discovery pages help people find public nonprofit profiles in communities where the registry has enough data.",
        "sections": [
            ("City Searches Are Specific", "Many useful searches include a city and a cause, such as food pantry nonprofits in Houston or animal rescue nonprofits in Austin."),
            ("Avoid Thin Results", "Daanaa builds city-and-cause pages only where the registry has enough public records to make the page useful."),
            ("Continue To Profiles", "Each page links directly to Daanaa organization profiles so users can act on the discovery."),
        ],
    },
    {
        "slug": "nonprofit-donation-records-tax-time",
        "title": "Organize Nonprofit Giving Records For Tax Time",
        "description": "How donors can use public nonprofit profiles and Daanaa's Giving Wallet idea to reduce giving record friction.",
        "answer": "Daanaa can help donors remember nonprofit profiles and giving intent, but it is not tax advice, a donation processor, or a receipt issuer.",
        "sections": [
            ("Records Matter", "For donors who itemize, charitable giving records can matter at tax time. Donors should rely on official guidance or a tax professional for tax questions."),
            ("Profiles Help Memory", "Stable nonprofit profile pages can help donors remember which organizations they supported or wanted to support."),
            ("Daanaa Does Not Handle Funds", "Daanaa does not process donations, hold donor funds, or issue donation receipts."),
        ],
    },
    {
        "slug": "how-nonprofits-get-found-online",
        "title": "How Nonprofits Get Found Online",
        "description": "A guide for nonprofit operators preparing to improve public discovery and claim profile context on Daanaa.",
        "answer": "Nonprofits get found online when identity, EIN, location, mission, public records, and stable profile links are clear enough for donors, search engines, and AI tools to understand.",
        "sections": [
            ("Discovery Is Infrastructure", "A nonprofit can be real and important but still hard to find if its public signals are fragmented."),
            ("Start With Identity", "Official name, EIN, city, state, website, mission, and contact paths help people and machines understand the organization."),
            ("Prepare To Claim", "Daanaa is building claim paths so nonprofits can improve public context while keeping source transparency intact."),
        ],
    },
    {
        "slug": "free-nonprofit-directory-listing",
        "title": "Free Nonprofit Directory Listing",
        "description": "Daanaa is free for nonprofits and does not sell profile treatment, trust language, peer context, or discovery priority.",
        "answer": "Daanaa public nonprofit profiles are free for nonprofits; organizations cannot pay for better profile treatment or discovery priority.",
        "sections": [
            ("Free Matters", "Smaller nonprofits should not be excluded from discovery because they cannot afford marketing or paid placement."),
            ("No Paid Profile Treatment", "Daanaa does not sell better nonprofit profile treatment, trust language, peer context, or discovery priority."),
            ("Claim Paths Are For Accuracy", "Claiming should help nonprofits correct and enrich public context, not influence discovery priority."),
        ],
    },

]

STATE_CATEGORY_PAIRS = [
    ("CA", "D"), ("CA", "B"), ("CA", "P"), ("CA", "O"), ("CA", "K"),
    ("TX", "D"), ("TX", "B"), ("TX", "P"), ("TX", "O"), ("TX", "K"),
    ("NY", "A"), ("NY", "B"), ("NY", "P"), ("NY", "L"), ("NY", "S"),
    ("FL", "D"), ("FL", "E"), ("FL", "P"), ("FL", "O"), ("FL", "N"),
    ("IL", "B"), ("IL", "K"), ("IL", "P"), ("IL", "A"), ("IL", "S"),
    ("PA", "B"), ("PA", "P"), ("PA", "E"), ("PA", "O"), ("PA", "D"),
    ("OH", "B"), ("OH", "P"), ("OH", "K"), ("OH", "N"), ("OH", "S"),
    ("GA", "B"), ("GA", "P"), ("GA", "O"), ("GA", "K"), ("GA", "D"),
    ("NC", "B"), ("NC", "P"), ("NC", "E"), ("NC", "O"), ("NC", "S"),
    ("MI", "B"), ("MI", "P"), ("MI", "K"), ("MI", "D"), ("MI", "S"),
]


def slugify(value: str) -> str:
    out = []
    for ch in value.lower():
        out.append(ch if ch.isalnum() else "-")
    return "-".join(part for part in "".join(out).split("-") if part)


def open_readonly() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB.resolve()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def shell(title: str, description: str, canonical: str, body: str, faq: list[tuple[str, str]] | None = None, item_rows: list[sqlite3.Row] | None = None) -> str:
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "url": canonical,
                "name": title,
                "description": description,
                "publisher": {"@type": "Organization", "name": "Daanaa", "url": PROFILE_BASE_URL},
            }
        ],
    }
    if faq:
        schema["@graph"].append({
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in faq
            ],
        })
    if item_rows:
        schema["@graph"].append({
            "@type": "ItemList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": idx + 1,
                    "url": f"{PROFILE_BASE_URL}/org/{''.join(ch for ch in str(row['EIN']) if ch.isdigit()).zfill(9)}",
                    "name": row["organization_name"],
                }
                for idx, row in enumerate(item_rows)
            ],
        })
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} | Daanaa</title>
  <meta name="description" content="{html.escape(description)}">
  <link rel="canonical" href="{canonical}">
</head>
<body>
  <main>
{body}
    <script type="application/ld+json">
{json.dumps(schema, indent=2)}
    </script>
  </main>
</body>
</html>
"""


def sample_orgs(conn: sqlite3.Connection, state: str | None = None, category: str | None = None) -> tuple[list[sqlite3.Row], int]:
    where = [
        "EIN IS NOT NULL AND EIN != ''",
        "organization_name IS NOT NULL AND organization_name != ''",
        "org_status = 'active'",
        "CAST(deductibility AS TEXT) = '1'",
    ]
    params: list[object] = []
    if state:
        where.append("STATE = ?")
        params.append(state)
    if category:
        where.append("substr(coalesce(nullif(NTEE1, ''), nullif(NTEECC, ''), 'Z'), 1, 1) = ?")
        params.append(category)
    base = " AND ".join(where)
    count = int(conn.execute(f"SELECT COUNT(*) FROM registry_enriched WHERE {base}", params).fetchone()[0])
    sql = f"""
        SELECT EIN, organization_name, CITY, STATE,
               substr(coalesce(nullif(NTEE1, ''), nullif(NTEECC, ''), 'Z'), 1, 1) AS category,
               total_revenue, latest_tax_year, is_hidden_gem
        FROM registry_enriched
        WHERE {base}
          AND is_hidden_gem = 1
          AND total_revenue >= {REVENUE_FLOOR}
        ORDER BY COALESCE(latest_tax_year, 0) DESC,
                 COALESCE(peer_percentile, ntee1_percentile, merit_score_v5, merit_score, 0) DESC,
                 total_revenue ASC,
                 EIN ASC
        LIMIT {SAMPLE_LIMIT}
    """
    rows = list(conn.execute(sql, params))
    if rows:
        return rows, count
    fallback_sql = f"""
        SELECT EIN, organization_name, CITY, STATE,
               substr(coalesce(nullif(NTEE1, ''), nullif(NTEECC, ''), 'Z'), 1, 1) AS category,
               total_revenue, latest_tax_year, is_hidden_gem
        FROM registry_enriched
        WHERE {base}
          AND total_revenue >= {REVENUE_FLOOR}
        ORDER BY COALESCE(latest_tax_year, 0) DESC,
                 total_revenue ASC,
                 EIN ASC
        LIMIT {SAMPLE_LIMIT}
    """
    return list(conn.execute(fallback_sql, params)), count


def org_list(rows: list[sqlite3.Row]) -> str:
    items = []
    for row in rows:
        ein = ''.join(ch for ch in str(row['EIN']) if ch.isdigit()).zfill(9)
        name = html.escape(row['organization_name'] or '')
        city = html.escape(row['CITY'] or '')
        state = html.escape(row['STATE'] or '')
        category = html.escape(NTEE_MAJOR.get((row['category'] or 'Z').upper(), 'Unclassified or not yet categorized'))
        items.append(f'        <li><a href="{PROFILE_BASE_URL}/org/{ein}">{name}</a> — {city}, {state}; {category}</li>')
    return "\n".join(items)


def cta_block() -> str:
    return f"""      <h2>Continue On Daanaa</h2>
      <p><a href="{PROFILE_BASE_URL}">Search public nonprofit profiles on Daanaa</a>. Nonprofit profile pages live on <code>daanaa.org</code>, while this overlay helps search engines and AI tools discover the public directory.</p>
      <p>Daanaa does not process donations or hold donor funds. Nonprofits cannot pay for better profile treatment, trust language, peer context, or discovery priority.</p>"""


def write_general_pages() -> list[str]:
    out = PUBLIC / "intent"
    out.mkdir(parents=True, exist_ok=True)
    urls = []
    index_items = []
    for page in GENERAL_PAGES:
        url = f"{BASE_URL}/intent/{page['slug']}.html"
        urls.append(url)
        sections = [f"      <h2>Quick Answer</h2>\n      <p>{html.escape(page['answer'])}</p>"]
        for heading, paragraph in page["sections"]:
            sections.append(f"      <h2>{html.escape(heading)}</h2>\n      <p>{html.escape(paragraph)}</p>")
        body = f"""    <article>
      <h1>{html.escape(page['title'])}</h1>
      <p>{html.escape(page['description'])}</p>
{chr(10).join(sections)}
{cta_block()}
    </article>"""
        faq = [(page["title"], page["answer"])]
        (out / f"{page['slug']}.html").write_text(shell(page["title"], page["description"], url, body, faq), encoding="utf-8")
        index_items.append(f'        <li><a href="/intent/{page["slug"]}.html">{html.escape(page["title"])}</a></li>')
    index_url = f"{BASE_URL}/intent/index.html"
    urls.append(index_url)
    body = f"""    <article>
      <h1>Nonprofit Discovery Answers</h1>
      <p>These pages answer common donor, volunteer, nonprofit, and AI-search questions, then direct users to Daanaa public nonprofit profiles.</p>
      <ul>
{chr(10).join(index_items)}
      </ul>
    </article>"""
    (out / "index.html").write_text(shell("Nonprofit Discovery Answers", "Intent-first nonprofit discovery answers that direct users to Daanaa public nonprofit profiles.", index_url, body), encoding="utf-8")
    return urls



def top_states(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    sql = """
        SELECT STATE AS state, COUNT(*) AS count
        FROM registry_enriched
        WHERE EIN IS NOT NULL AND EIN != ''
          AND organization_name IS NOT NULL AND organization_name != ''
          AND org_status = 'active'
          AND CAST(deductibility AS TEXT) = '1'
          AND STATE IS NOT NULL AND STATE != ''
        GROUP BY STATE
        ORDER BY count DESC, STATE ASC
        LIMIT ?
    """
    return [(str(row["state"]).upper(), STATE_NAMES.get(str(row["state"]).upper(), str(row["state"]).upper())) for row in conn.execute(sql, (TOP_STATE_LIMIT,)) if str(row["state"]).upper() in STATE_NAMES]


def top_categories(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    sql = """
        SELECT substr(coalesce(nullif(NTEE1, ''), nullif(NTEECC, ''), 'Z'), 1, 1) AS category, COUNT(*) AS count
        FROM registry_enriched
        WHERE EIN IS NOT NULL AND EIN != ''
          AND organization_name IS NOT NULL AND organization_name != ''
          AND org_status = 'active'
          AND CAST(deductibility AS TEXT) = '1'
        GROUP BY category
        ORDER BY count DESC, category ASC
    """
    pairs = []
    for row in conn.execute(sql):
        code = str(row["category"]).upper()
        if code in NTEE_MAJOR:
            pairs.append((code, NTEE_MAJOR[code]))
        if len(pairs) >= TOP_CATEGORY_LIMIT:
            break
    return pairs


def top_city_category_pairs(conn: sqlite3.Connection) -> list[tuple[str, str, str, str, int]]:
    sql = """
        SELECT CITY AS city, STATE AS state,
               substr(coalesce(nullif(NTEE1, ''), nullif(NTEECC, ''), 'Z'), 1, 1) AS category,
               COUNT(*) AS count
        FROM registry_enriched
        WHERE EIN IS NOT NULL AND EIN != ''
          AND organization_name IS NOT NULL AND organization_name != ''
          AND org_status = 'active'
          AND CAST(deductibility AS TEXT) = '1'
          AND CITY IS NOT NULL AND CITY != ''
          AND STATE IS NOT NULL AND STATE != ''
        GROUP BY CITY, STATE, category
        HAVING count >= ?
        ORDER BY count DESC, STATE ASC, CITY ASC, category ASC
        LIMIT ?
    """
    pairs = []
    for row in conn.execute(sql, (MIN_CITY_CAUSE_RECORDS, TOP_CITY_CAUSE_LIMIT)):
        state = str(row["state"]).upper()
        category = str(row["category"]).upper()
        if state in STATE_NAMES and category in NTEE_MAJOR:
            pairs.append((str(row["city"]).title(), state, STATE_NAMES[state], category, int(row["count"])))
    return pairs

def write_state_category_pages(conn: sqlite3.Connection) -> list[str]:
    out = PUBLIC / "find"
    out.mkdir(parents=True, exist_ok=True)
    urls = []
    index_items = []
    seen_pairs = set()
    generated_pairs = [(state, category) for state, _ in top_states(conn) for category, _ in top_categories(conn)]
    generated_pairs.extend(STATE_CATEGORY_PAIRS)
    for state, category in generated_pairs:
        if (state, category) in seen_pairs:
            continue
        seen_pairs.add((state, category))
        state_name = STATE_NAMES[state]
        category_name = NTEE_MAJOR[category]
        slug = f"{slugify(category_name)}-nonprofits-in-{slugify(state_name)}"
        title = f"Find {category_name} Nonprofits In {state_name}"
        description = f"Use Daanaa to find public {category_name.lower()} nonprofit profiles in {state_name}."
        url = f"{BASE_URL}/find/{slug}.html"
        rows, count = sample_orgs(conn, state=state, category=category)
        answer = f"Daanaa indexes {count:,} active deductible {category_name.lower()} nonprofit records in {state_name} and links users to stable public profile pages on daanaa.org."
        body = f"""    <article>
      <h1>{html.escape(title)}</h1>
      <p>{html.escape(description)}</p>
      <h2>Quick Answer</h2>
      <p>{html.escape(answer)}</p>
      <h2>Sample Public Profiles On Daanaa</h2>
      <p>This sample favors hidden-gem profiles with recent public financial context where available. It is a discovery starting point, not a ranking, endorsement, or paid placement.</p>
      <ul>
{org_list(rows)}
      </ul>
{cta_block()}
    </article>"""
        (out / f"{slug}.html").write_text(shell(title, description, url, body, [(title, answer)], rows), encoding="utf-8")
        urls.append(url)
        index_items.append(f'        <li><a href="/find/{slug}.html">{html.escape(title)}</a> — {count:,} records</li>')
    index_url = f"{BASE_URL}/find/index.html"
    urls.append(index_url)
    body = f"""    <article>
      <h1>Find Nonprofits By Cause And State</h1>
      <p>These discovery pages answer cause-and-place searches, then direct users to Daanaa public nonprofit profiles.</p>
      <ul>
{chr(10).join(index_items)}
      </ul>
    </article>"""
    (out / "index.html").write_text(shell("Find Nonprofits By Cause And State", "Cause-and-state nonprofit discovery pages that direct users to Daanaa public nonprofit profiles.", index_url, body), encoding="utf-8")
    return urls



def write_city_category_pages(conn: sqlite3.Connection) -> list[str]:
    out = PUBLIC / "local"
    out.mkdir(parents=True, exist_ok=True)
    urls = []
    index_items = []
    for city, state, state_name, category, count_hint in top_city_category_pairs(conn):
        category_name = NTEE_MAJOR[category]
        slug = f"{slugify(category_name)}-nonprofits-in-{slugify(city)}-{state.lower()}"
        title = f"Find {category_name} Nonprofits In {city}, {state}"
        description = f"Use Daanaa to find public {category_name.lower()} nonprofit profiles in {city}, {state_name}."
        url = f"{BASE_URL}/local/{slug}.html"
        rows, count = sample_orgs(conn, state=state, category=category)
        answer = f"Daanaa indexes {count:,} active deductible {category_name.lower()} nonprofit records in {state_name}, including public profiles relevant to {city} searches."
        # Use city-specific sample if available; fallback to state/category sample for profile depth.
        city_rows, city_count = sample_city_orgs(conn, city=city.upper(), state=state, category=category)
        if city_rows:
            rows = city_rows
            answer = f"Daanaa indexes {city_count:,} active deductible {category_name.lower()} nonprofit records in {city}, {state} and links users to stable public profile pages on daanaa.org."
        body = f"""    <article>
      <h1>{html.escape(title)}</h1>
      <p>{html.escape(description)}</p>
      <h2>Quick Answer</h2>
      <p>{html.escape(answer)}</p>
      <h2>Sample Public Profiles On Daanaa</h2>
      <p>This sample favors hidden-gem profiles with recent public financial context where available. It is a discovery starting point, not a ranking, endorsement, or paid placement.</p>
      <ul>
{org_list(rows)}
      </ul>
{cta_block()}
    </article>"""
        (out / f"{slug}.html").write_text(shell(title, description, url, body, [(title, answer)], rows), encoding="utf-8")
        urls.append(url)
        index_items.append(f'        <li><a href="/local/{slug}.html">{html.escape(title)}</a> — {city_count if city_rows else count_hint:,} records</li>')
    index_url = f"{BASE_URL}/local/index.html"
    urls.append(index_url)
    body = f"""    <article>
      <h1>Find Local Nonprofits By City And Cause</h1>
      <p>These local discovery pages answer city-and-cause searches, then direct users to Daanaa public nonprofit profiles.</p>
      <ul>
{chr(10).join(index_items)}
      </ul>
    </article>"""
    (out / "index.html").write_text(shell("Find Local Nonprofits By City And Cause", "City-and-cause nonprofit discovery pages that direct users to Daanaa public nonprofit profiles.", index_url, body), encoding="utf-8")
    return urls


def sample_city_orgs(conn: sqlite3.Connection, city: str, state: str, category: str) -> tuple[list[sqlite3.Row], int]:
    where = """
        EIN IS NOT NULL AND EIN != ''
        AND organization_name IS NOT NULL AND organization_name != ''
        AND org_status = 'active'
        AND CAST(deductibility AS TEXT) = '1'
        AND upper(CITY) = ?
        AND STATE = ?
        AND substr(coalesce(nullif(NTEE1, ''), nullif(NTEECC, ''), 'Z'), 1, 1) = ?
    """
    params = (city, state, category)
    count = int(conn.execute(f"SELECT COUNT(*) FROM registry_enriched WHERE {where}", params).fetchone()[0])
    sql = f"""
        SELECT EIN, organization_name, CITY, STATE,
               substr(coalesce(nullif(NTEE1, ''), nullif(NTEECC, ''), 'Z'), 1, 1) AS category,
               total_revenue, latest_tax_year, is_hidden_gem
        FROM registry_enriched
        WHERE {where}
          AND total_revenue >= {REVENUE_FLOOR}
        ORDER BY is_hidden_gem DESC,
                 COALESCE(latest_tax_year, 0) DESC,
                 total_revenue ASC,
                 EIN ASC
        LIMIT {SAMPLE_LIMIT}
    """
    return list(conn.execute(sql, params)), count

def write_sitemap(urls: list[str]) -> None:
    today = date.today().isoformat()
    with (PUBLIC / "intent-pages.xml").open("w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for url in sorted(set(urls)):
            f.write("  <url>\n")
            f.write(f"    <loc>{html.escape(url, quote=True)}</loc>\n")
            f.write(f"    <lastmod>{today}</lastmod>\n")
            f.write("  </url>\n")
        f.write("</urlset>\n")


def write_report(urls: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "url_count": len(set(urls)),
        "sitemap": f"{BASE_URL}/intent-pages.xml",
        "goal": "Capture non-brand nonprofit discovery intent and direct users to daanaa.org profiles.",
        "urls": sorted(set(urls)),
    }
    (REPORTS / "intent-discovery-pages.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = ["# Intent Discovery Pages", "", f"Generated: {payload['generated_at']}", f"URLs: {payload['url_count']}", "", payload["goal"], "", "## URLs", ""]
    md.extend(f"- {url}" for url in payload["urls"])
    (REPORTS / "intent-discovery-pages.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    urls = write_general_pages()
    with open_readonly() as conn:
        urls.extend(write_state_category_pages(conn))
        urls.extend(write_city_category_pages(conn))
    write_sitemap(urls)
    write_report(urls)
    print(f"Wrote {len(set(urls))} intent URLs")
    print(REPORTS / "intent-discovery-pages.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
