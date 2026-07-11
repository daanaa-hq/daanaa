#!/usr/bin/env python3
"""Build data-driven visibility pages and outreach assets for the overlay."""

from __future__ import annotations

import hashlib
import html
import json
import re
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "merit_registry.db"
PUBLIC = ROOT / "visibility" / "public"
REPORTS = ROOT / "visibility" / "reports"
BASE_URL = "https://data.daanaa.org"
PROFILE_BASE_URL = "https://daanaa.org"
ROTATION_MONTH = date.today().strftime("%Y-%m")
NEXT_REFRESH = f"{date.today().year + (1 if date.today().month == 12 else 0):04d}-{1 if date.today().month == 12 else date.today().month + 1:02d}-01"
SAMPLE_LIMIT = 25
CANDIDATE_LIMIT = 240
REVENUE_FLOOR = 10_000

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
    "Y": "Mutual and Membership Benefit",
    "Z": "Unclassified or not yet categorized",
    "0": "Unclassified",
}

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "PR": "Puerto Rico", "GU": "Guam", "VI": "U.S. Virgin Islands",
    "AS": "American Samoa", "MP": "Northern Mariana Islands",
}

GUIDES = [
    {
        "slug": "how-to-give-locally",
        "title": "How To Give Locally Without Getting Lost",
        "description": "A practical donor guide for finding local nonprofits, reading public context, and choosing a clear next step.",
        "sections": [
            ("Start Near The Need", "Local giving often starts with a place, a school, a neighborhood, a faith community, or a problem someone sees directly. Daanaa helps turn that instinct into a search path by connecting public nonprofit records to stable profiles."),
            ("Use Public Data As A Map", "Public data can confirm identity, EIN, city, state, and broad category. It should not be treated as the full story. A sparse profile can mean the nonprofit has limited administrative capacity or has not claimed its page yet."),
            ("Look For A Clear Next Step", "A good giving path should help a person learn, give, volunteer, or return later. Daanaa does not process donations or hold donor funds; when giving paths are available, they should lead to the nonprofit's own channel or another independent route."),
        ],
    },
    {
        "slug": "choose-a-nonprofit-without-hype",
        "title": "How To Choose A Nonprofit Without Relying On Hype",
        "description": "A humane donor guide for using public nonprofit information without reducing organizations to marketing polish.",
        "sections": [
            ("Marketing Is Not The Mission", "Some nonprofits are easy to find because they have staff, media reach, and strong communications. Others are quiet but deeply rooted. Daanaa's discovery model is designed to make smaller nonprofits easier to find without treating visibility as worth."),
            ("Separate Signals", "Identity, public filings, claim status, donation paths, volunteer paths, and peer context should be read as separate signals. No single field should become a shortcut for trust."),
            ("Ask Better Questions", "Useful questions include: who does this organization serve, where does it work, what public data exists, what is missing, and how can the nonprofit correct or enrich the page?"),
        ],
    },
    {
        "slug": "organize-giving-for-tax-time",
        "title": "How To Organize Giving For Tax Time",
        "description": "How donors can keep giving records easier to find while relying on official tax guidance and their own advisors.",
        "sections": [
            ("Recordkeeping Reduces Friction", "Giving is easier to repeat when the records are not scattered. Donors who itemize deductions need their own records and should rely on IRS guidance or a tax professional for tax questions."),
            ("Use The Wallet As Memory", "Daanaa's Giving Wallet is intended to help a donor remember organizations, intent, and profile context. It is not tax advice, a receipt issuer, or a payment processor."),
            ("Keep The Handoff Clear", "Daanaa does not process donations, hold donor funds, or make giving activity public. The wallet supports follow-through without turning generosity into public performance."),
        ],
    },
    {
        "slug": "volunteer-when-you-cannot-give-money",
        "title": "How To Volunteer When You Cannot Give Money",
        "description": "A guide for people who want to support nonprofits through time, skills, knowledge, and care.",
        "sections": [
            ("Giving Is Broader Than A Payment", "Money matters, but it is not the only form of generosity. Time, knowledge, introductions, translation, operations help, and patient attention can also support a nonprofit's work."),
            ("Match Help To The Organization", "A volunteer path should respect the nonprofit's actual needs. As Daanaa profiles mature, claimed pages can help organizations show whether they need funds, volunteers, operational help, or subject-matter knowledge."),
            ("Protect Dignity", "Daanaa's goal is to make support easier to find without exposing donor identity, creating pressure, or turning generosity into performance."),
        ],
    },
    {
        "slug": "claim-your-nonprofit-profile-guide",
        "title": "How Nonprofits Can Prepare To Claim A Daanaa Profile",
        "description": "A beta-stage guide for nonprofits that want to improve public discovery while keeping source transparency intact.",
        "sections": [
            ("Find The Public Profile", "Daanaa profiles use a stable EIN-based URL. EIN values in data exports are nine digits; human-facing displays may show the same value as XX-XXXXXXX."),
            ("Prepare The Basics", "Useful claim information includes official name, website, mission, service area, contact path, donation path, volunteer needs, and corrections to public data."),
            ("No Paid Profile Treatment", "Daanaa is free for nonprofits. Organizations are not charged for listings or claims, and claim visibility is not dependent on paid promotion."),
        ],
    },
]


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def open_readonly() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB.resolve()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def query_counts(conn: sqlite3.Connection, group_expr: str, where_extra: str = "") -> list[sqlite3.Row]:
    sql = f"""
        SELECT {group_expr} AS key, COUNT(*) AS count
        FROM registry_enriched
        WHERE EIN IS NOT NULL AND EIN != ''
          AND organization_name IS NOT NULL AND organization_name != ''
          AND org_status = 'active'
          AND CAST(deductibility AS TEXT) = '1'
          {where_extra}
        GROUP BY key
        HAVING key IS NOT NULL AND key != ''
        ORDER BY count DESC, key ASC
    """
    return list(conn.execute(sql))


def _score_value(row: sqlite3.Row) -> float:
    for key in ["peer_percentile", "ntee1_percentile", "merit_score_v5", "merit_score"]:
        value = row[key]
        if value is not None:
            return float(value)
    return 0.0


def _rotation_value(row: sqlite3.Row) -> str:
    ein = ''.join(ch for ch in str(row["EIN"]) if ch.isdigit()).zfill(9)
    return hashlib.sha256(f"{ROTATION_MONTH}:{ein}".encode("utf-8")).hexdigest()


def _freshness_sort(row: sqlite3.Row) -> tuple[object, ...]:
    return (
        -(int(row["latest_tax_year"] or 0)),
        -_score_value(row),
        float(row["total_revenue"] or 0),
        ''.join(ch for ch in str(row["EIN"]) if ch.isdigit()).zfill(9),
    )


def _rotated_sample(rows: list[sqlite3.Row]) -> list[sqlite3.Row]:
    rotated = sorted(rows, key=_rotation_value)[:SAMPLE_LIMIT]
    return sorted(rotated, key=_freshness_sort)


def sample_orgs(conn: sqlite3.Connection, where: str, params: tuple[object, ...]) -> tuple[list[sqlite3.Row], str]:
    base_select = f"""
        SELECT EIN, organization_name, CITY, STATE, is_hidden_gem, total_revenue,
               peer_percentile, ntee1_percentile, merit_score_v5, merit_score, latest_tax_year,
               substr(coalesce(nullif(NTEE1, ''), nullif(NTEECC, ''), 'Z'), 1, 1) AS category
        FROM registry_enriched
        WHERE EIN IS NOT NULL AND EIN != ''
          AND organization_name IS NOT NULL AND organization_name != ''
          AND org_status = 'active'
          AND CAST(deductibility AS TEXT) = '1'
          AND {where}
    """
    candidate_order = f"""
        ORDER BY COALESCE(latest_tax_year, 0) DESC,
                 COALESCE(peer_percentile, ntee1_percentile, merit_score_v5, merit_score, 0) DESC,
                 total_revenue ASC,
                 EIN ASC
        LIMIT {CANDIDATE_LIMIT}
    """
    hidden_sql = base_select + f"""
          AND is_hidden_gem = 1
          AND total_revenue >= {REVENUE_FLOOR}
    """ + candidate_order
    rows = list(conn.execute(hidden_sql, params))
    if rows:
        return _rotated_sample(rows), f"monthly hidden-gem rotation for {ROTATION_MONTH}, with reported revenue of at least $10,000 and recent public financial context"

    fallback_sql = base_select + f"""
          AND total_revenue >= {REVENUE_FLOOR}
    """ + candidate_order
    rows = list(conn.execute(fallback_sql, params))
    if rows:
        return _rotated_sample(rows), f"monthly public-profile rotation for {ROTATION_MONTH}, with reported revenue of at least $10,000 and recent public financial context"

    last_resort_sql = base_select + f"""
        ORDER BY COALESCE(latest_tax_year, 0) DESC,
                 COALESCE(peer_percentile, ntee1_percentile, merit_score_v5, merit_score, 0) DESC,
                 EIN ASC
        LIMIT {SAMPLE_LIMIT}
    """
    return list(conn.execute(last_resort_sql, params)), "public profiles with limited financial context"


def directory_filter(list_id: str, label: str, placeholder: str) -> str:
    safe_list_id = html.escape(list_id, quote=True)
    input_id = f"{safe_list_id}-filter"
    status_id = f"{safe_list_id}-status"
    return f"""      <div class="directory-tools">
        <label for="{input_id}">{html.escape(label)}</label>
        <input type="search" id="{input_id}" placeholder="{html.escape(placeholder, quote=True)}" aria-controls="{safe_list_id}" aria-describedby="{status_id}" data-directory-filter data-status-id="{status_id}" autocomplete="off">
        <p class="filter-status" id="{status_id}" aria-live="polite"></p>
      </div>"""


def filterable_directory(list_id: str, label: str, placeholder: str, items: str) -> str:
    safe_list_id = html.escape(list_id, quote=True)
    return (
        directory_filter(list_id, label, placeholder)
        + f'\n      <ul id="{safe_list_id}">\n{items}\n      </ul>'
    )


def page_shell(title: str, description: str, canonical: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} | Daanaa</title>
  <meta name="description" content="{html.escape(description)}">
  <link rel="canonical" href="{canonical}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600&amp;family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500;1,600&amp;family=DM+Sans:wght@400;500;600&amp;display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --deep-navy: #0A1628;
      --dark-surface: #111D2E;
      --warm-cream: #F5F0EB;
      --soft-gold: #C9A96E;
      --link-gold: #7A5C2E;
      --cool-grey: #374151;
      --muted-cream: #D4CCBF;
      --light-cream: #EDE8E0;
      --light-grey: #E5E0DB;
      --white: #FFFFFF;
    }}
    html {{ scroll-behavior: smooth; }}
    body {{
      font-family: 'DM Sans', Inter, system-ui, sans-serif;
      background: var(--warm-cream);
      color: var(--cool-grey);
      line-height: 1.6;
      min-height: 100vh;
      -webkit-font-smoothing: antialiased;
    }}
    a {{
      color: var(--link-gold);
      text-decoration-thickness: 1px;
      text-underline-offset: 3px;
    }}
    a:hover {{ color: var(--deep-gold, #6B552D); }}
    a:focus-visible, input:focus-visible {{
      outline: 3px solid rgba(201, 169, 110, 0.5);
      outline-offset: 3px;
    }}
    .site-header {{
      position: sticky;
      top: 0;
      z-index: 20;
      background: rgba(255, 255, 255, 0.97);
      border-bottom: 1px solid var(--light-grey);
      backdrop-filter: blur(12px);
    }}
    .nav-shell {{
      width: calc(100% - 48px);
      max-width: 1200px;
      margin: 0 auto;
      min-height: 72px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 28px;
    }}
    .brand {{
      color: var(--deep-navy);
      font-family: Cinzel, serif;
      font-size: 18px;
      font-weight: 600;
      letter-spacing: 0;
      text-decoration: none;
    }}
    .nav-links {{
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 24px;
      margin-left: auto;
    }}
    .nav-links a {{
      color: var(--cool-grey);
      font-size: 13px;
      font-weight: 500;
      text-decoration: none;
    }}
    .nav-links a:hover {{ color: var(--deep-navy); }}
    .nav-links .nav-cta {{
      min-height: 40px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0 18px;
      border-radius: 999px;
      background: var(--deep-navy);
      color: var(--warm-cream);
    }}
    .nav-links .nav-cta:hover {{
      background: var(--dark-surface);
      color: var(--white);
    }}
    main {{ background: var(--warm-cream); }}
    .page-shell {{
      width: calc(100% - 48px);
      max-width: 1200px;
      margin: 0 auto;
      padding: 38px 0 88px;
    }}
    .breadcrumb {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 28px;
      color: var(--cool-grey);
      font-size: 12px;
    }}
    .breadcrumb a {{ color: var(--cool-grey); }}
    article {{ max-width: 980px; }}
    h1 {{
      max-width: 900px;
      font-family: 'Cormorant Garamond', Georgia, serif;
      font-size: 48px;
      font-weight: 600;
      font-style: italic;
      color: var(--deep-navy);
      line-height: 1.05;
      letter-spacing: 0;
      margin-bottom: 18px;
    }}
    h2 {{
      font-family: 'Cormorant Garamond', Georgia, serif;
      font-size: 28px;
      font-weight: 600;
      color: var(--deep-navy);
      letter-spacing: 0;
      margin: 44px 0 12px;
    }}
    p {{
      font-size: 16px;
      max-width: 780px;
      margin-bottom: 14px;
      color: var(--cool-grey);
    }}
    ul {{
      list-style: none;
      margin: 24px 0;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
    }}
    li {{
      min-width: 0;
      font-size: 15px;
      padding: 15px 16px;
      background: var(--white);
      border: 1px solid var(--light-grey);
      border-radius: 6px;
      overflow-wrap: anywhere;
    }}
    li a {{
      color: var(--link-gold);
      font-weight: 600;
    }}
    .directory-tools {{
      max-width: 620px;
      margin: 30px 0 18px;
    }}
    .directory-tools label {{
      display: block;
      margin-bottom: 8px;
      color: var(--deep-navy);
      font-size: 13px;
      font-weight: 600;
    }}
    .directory-tools input {{
      width: 100%;
      min-height: 46px;
      padding: 0 15px;
      border: 1px solid var(--light-grey);
      border-radius: 6px;
      background: var(--white);
      color: var(--deep-navy);
      font: inherit;
      font-size: 15px;
    }}
    .directory-tools input::placeholder {{ color: #6B7280; }}
    .filter-status {{
      min-height: 20px;
      margin: 7px 0 0;
      font-size: 12px;
    }}
    .site-footer {{
      background: var(--deep-navy);
      color: var(--muted-cream);
    }}
    .footer-shell {{
      width: calc(100% - 48px);
      max-width: 1200px;
      min-height: 156px;
      margin: 0 auto;
      padding: 32px 0;
      display: grid;
      grid-template-columns: minmax(220px, 1fr) auto;
      align-items: center;
      gap: 32px;
    }}
    .footer-brand {{
      margin-bottom: 8px;
      color: var(--warm-cream);
      font-family: Cinzel, serif;
      font-size: 16px;
      font-weight: 600;
      letter-spacing: 0;
    }}
    .site-footer p {{
      margin: 0;
      color: var(--muted-cream);
      font-size: 13px;
      max-width: 620px;
    }}
    .footer-links {{
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 18px;
    }}
    .footer-links a {{
      color: var(--warm-cream);
      font-size: 13px;
    }}
    @media (max-width: 760px) {{
      .nav-shell, .page-shell, .footer-shell {{
        width: calc(100% - 32px);
      }}
      .nav-links {{ gap: 12px; }}
      .nav-extra {{ display: none; }}
      .page-shell {{ padding: 28px 0 64px; }}
      h1 {{ font-size: 36px; }}
      h2 {{ font-size: 25px; }}
      ul {{ grid-template-columns: 1fr; }}
      .footer-shell {{ grid-template-columns: 1fr; }}
      .footer-links {{ justify-content: flex-start; }}
    }}
  </style>
</head>
<body>
  <header class="site-header">
    <nav class="nav-shell" aria-label="Main navigation">
      <a class="brand" href="https://daanaa.org">Daanaa</a>
      <div class="nav-links">
        <a class="nav-extra" href="https://daanaa.org/methodology">How it works</a>
        <a class="nav-extra" href="https://daanaa.org/research">Research</a>
        <a class="nav-extra" href="https://daanaa.org/about">About</a>
        <a class="nav-cta" href="https://daanaa.org/directory">Explore nonprofits</a>
      </div>
    </nav>
  </header>
  <main>
    <div class="page-shell">
      <nav class="breadcrumb" aria-label="Breadcrumb">
        <a href="https://daanaa.org">Home</a>
        <span aria-hidden="true">/</span>
        <span aria-current="page">{html.escape(title)}</span>
      </nav>
{body}
    </div>
  </main>
  <footer class="site-footer">
    <div class="footer-shell">
      <div>
        <div class="footer-brand">Daanaa</div>
        <p>Independent nonprofit discovery built from public records. Discovery pages are not rankings, endorsements, or paid placements.</p>
      </div>
      <nav class="footer-links" aria-label="Footer navigation">
        <a href="https://daanaa.org/directory">Directory</a>
        <a href="https://daanaa.org/methodology">Methodology</a>
        <a href="https://daanaa.org/for-nonprofits">For nonprofits</a>
        <a href="https://daanaa.org/about">About</a>
        <a href="https://daanaa.org/privacy">Privacy</a>
        <a href="https://daanaa.org/legal">Legal</a>
      </nav>
    </div>
  </footer>
  <script>
    (() => {{
      const inputs = document.querySelectorAll('[data-directory-filter]');
      inputs.forEach((input) => {{
        const list = document.getElementById(input.getAttribute('aria-controls'));
        const status = document.getElementById(input.dataset.statusId);
        if (!list || !status) return;
        const items = Array.from(list.querySelectorAll(':scope > li'));
        const update = () => {{
          const query = input.value.trim().toLocaleLowerCase();
          let visible = 0;
          items.forEach((item) => {{
            const matches = !query || item.textContent.toLocaleLowerCase().includes(query);
            item.hidden = !matches;
            if (matches) visible += 1;
          }});
          status.textContent = visible.toLocaleString() + (visible === 1 ? ' result' : ' results');
        }};
        input.addEventListener('input', update);
        update();
      }});
    }})();
  </script>
</body>
</html>
"""


def org_list(rows: list[sqlite3.Row]) -> str:
    items = []
    for row in rows:
        ein = ''.join(ch for ch in str(row['EIN']) if ch.isdigit()).zfill(9)
        name = html.escape(row['organization_name'] or '')
        city = html.escape(row['CITY'] or '')
        state = html.escape(row['STATE'] or '')
        category = NTEE_MAJOR.get((row['category'] or 'Z').upper(), 'Unclassified or not yet categorized')
        items.append(f'      <li><a href="{PROFILE_BASE_URL}/org/{ein}">{name}</a> — {city}, {state}; {html.escape(category)}</li>')
    return "\n".join(items)


def write_state_pages(conn: sqlite3.Connection, urls: list[str]) -> list[dict[str, object]]:
    out = PUBLIC / "nonprofits" / "state"
    out.mkdir(parents=True, exist_ok=True)
    states = [row for row in query_counts(conn, "STATE", "AND STATE IS NOT NULL AND STATE != ''") if str(row['key']).upper() in STATE_NAMES]
    cards = []
    metadata = []
    for row in states:
        code = str(row['key']).upper()
        count = int(row['count'])
        name = STATE_NAMES[code]
        slug = code.lower()
        url = f"{BASE_URL}/nonprofits/state/{slug}.html"
        urls.append(url)
        samples, sample_source = sample_orgs(conn, "STATE = ?", (code,))
        body = f"""    <article>
      <h1>{html.escape(name)} Nonprofit Directory</h1>
      <p>Daanaa currently indexes {count:,} active deductible nonprofit records in {html.escape(name)}. This page is a public discovery starting point for donors, volunteers, civic partners, search engines, and AI tools.</p>
      <p>These profiles are not rankings and are not paid placements. They connect public records to stable Daanaa profile URLs so people can find nonprofits, read source context, and return later to give, volunteer, or learn more.</p>
      <h2>Hidden Gem Sample Profiles</h2>
      <p>This monthly sample is drawn from Daanaa hidden-gem profiles when available: smaller, financially healthy, lower profile organizations with recent public financial context. Samples require reported revenue of at least $10,000 and rotate monthly so more nonprofits can become visible over time. This is a discovery starting point, not an endorsement or ranking.</p>
      <p>Sample source: {sample_source}. Next scheduled refresh: {NEXT_REFRESH}.</p>
      <ul>
{org_list(samples)}
      </ul>
      <h2>Use This Responsibly</h2>
      <p>A sparse profile does not mean weak work. Smaller nonprofits may have limited administrative capacity or unclaimed public pages. Daanaa is free for nonprofits, does not process donations or hold donor funds, and keeps public data, claim status, donation paths, and volunteer paths separate.</p>
      <p><a href="{BASE_URL}/claim-nonprofit-page.html">Claim nonprofit page information</a></p>
    </article>"""
        (out / f"{slug}.html").write_text(page_shell(f"{name} Nonprofit Directory", f"Find public nonprofit profiles in {name} using Daanaa's independent nonprofit discovery overlay.", url, body), encoding="utf-8")
        cards.append(f'      <li><a href="/nonprofits/state/{slug}.html">{html.escape(name)}</a> — {count:,} records</li>')
        metadata.append({"state": code, "name": name, "count": count, "url": url, "sample_source": sample_source})
    index_url = f"{BASE_URL}/nonprofits/state/index.html"
    urls.append(index_url)
    body = f"""    <article>
      <h1>Nonprofit Directory By State</h1>
      <p>Daanaa publishes state discovery pages so donors, volunteers, nonprofit operators, civic partners, search engines, and AI tools can find public nonprofit profiles more easily.</p>
      <p>State counts are generated from active deductible nonprofit records already present in the Daanaa registry. These pages are discovery maps, not rankings or endorsements.</p>
{filterable_directory("state-directory", "Filter states", "Search by state or territory", chr(10).join(cards))}
    </article>"""
    (out / "index.html").write_text(page_shell("Nonprofit Directory By State", "Browse public Daanaa nonprofit discovery pages by state.", index_url, body), encoding="utf-8")
    return metadata


def write_category_pages(conn: sqlite3.Connection, urls: list[str]) -> list[dict[str, object]]:
    out = PUBLIC / "nonprofits" / "category"
    out.mkdir(parents=True, exist_ok=True)
    categories = query_counts(conn, "substr(coalesce(nullif(NTEE1, ''), nullif(NTEECC, ''), 'Z'), 1, 1)")
    cards = []
    metadata = []
    for row in categories:
        code = str(row['key']).upper()
        if code not in NTEE_MAJOR:
            continue
        count = int(row['count'])
        name = NTEE_MAJOR[code]
        slug = slugify(name)
        url = f"{BASE_URL}/nonprofits/category/{slug}.html"
        urls.append(url)
        samples, sample_source = sample_orgs(conn, "substr(coalesce(nullif(NTEE1, ''), nullif(NTEECC, ''), 'Z'), 1, 1) = ?", (code,))
        body = f"""    <article>
      <h1>{html.escape(name)} Nonprofit Directory</h1>
      <p>Daanaa currently indexes {count:,} active deductible nonprofit records in the {html.escape(name)} category. This page helps donors and volunteers start with public context before choosing a path to give, volunteer, or learn more.</p>
      <p>This is not a ranking, recommendation list, or paid placement. It is a discovery page generated from public-source-derived registry data.</p>
      <h2>Hidden Gem Sample Profiles</h2>
      <p>This monthly sample is drawn from Daanaa hidden-gem profiles when available: smaller, financially healthy, lower profile organizations with recent public financial context. Samples require reported revenue of at least $10,000 and rotate monthly so more nonprofits can become visible over time. This is a discovery starting point, not an endorsement or ranking.</p>
      <p>Sample source: {sample_source}. Next scheduled refresh: {NEXT_REFRESH}.</p>
      <ul>
{org_list(samples)}
      </ul>
      <h2>Use This Responsibly</h2>
      <p>Public category data can be incomplete or broad. Daanaa separates identity, peer context, claim status, donation paths, and volunteer paths so users can read the page with care. Nonprofits cannot pay for better profile treatment, trust language, peer context, or discovery priority.</p>
    </article>"""
        (out / f"{slug}.html").write_text(page_shell(f"{name} Nonprofit Directory", f"Find public nonprofit profiles in {name} using Daanaa's independent nonprofit discovery overlay.", url, body), encoding="utf-8")
        cards.append(f'      <li><a href="/nonprofits/category/{slug}.html">{html.escape(name)}</a> — {count:,} records</li>')
        metadata.append({"category": code, "name": name, "count": count, "url": url, "sample_source": sample_source})
    index_url = f"{BASE_URL}/nonprofits/category/index.html"
    urls.append(index_url)
    body = f"""    <article>
      <h1>Nonprofit Directory By Cause Category</h1>
      <p>Daanaa publishes category discovery pages so people can start from a cause area and then review public nonprofit profiles with care.</p>
      <p>Category pages are generated from NTEE-style public classification fields. They are not rankings, endorsements, or paid results.</p>
{filterable_directory("category-directory", "Filter cause categories", "Search by cause category", chr(10).join(cards))}
    </article>"""
    (out / "index.html").write_text(page_shell("Nonprofit Directory By Cause Category", "Browse public Daanaa nonprofit discovery pages by cause category.", index_url, body), encoding="utf-8")
    return metadata


def write_guides(urls: list[str]) -> list[dict[str, object]]:
    out = PUBLIC / "guides"
    out.mkdir(parents=True, exist_ok=True)
    cards = []
    metadata = []
    for guide in GUIDES:
        slug = guide["slug"]
        title = guide["title"]
        url = f"{BASE_URL}/guides/{slug}.html"
        urls.append(url)
        section_html = []
        for heading, paragraph in guide["sections"]:
            section_html.append(f"      <h2>{html.escape(heading)}</h2>\n      <p>{html.escape(paragraph)}</p>")
        body = f"""    <article>
      <h1>{html.escape(title)}</h1>
      <p>{html.escape(guide['description'])}</p>
{chr(10).join(section_html)}
      <h2>Daanaa's Stewardship Boundary</h2>
      <p>Daanaa is built to make giving easier without turning generosity into pressure. Daanaa does not process donations, hold donor funds, or make giving activity public. Nonprofits cannot pay for better profile treatment, trust language, peer context, or discovery priority.</p>
      <h2>Related Pages</h2>
      <ul>
        <li><a href="{BASE_URL}/open-data.html">Daanaa Visibility Overlay</a></li>
        <li><a href="{BASE_URL}/blog/philanthropy-belongs-to-everyone.html">Philanthropy belongs to everyone</a></li>
        <li><a href="{BASE_URL}/claim-nonprofit-page.html">Claim nonprofit page</a></li>
      </ul>
    </article>"""
        (out / f"{slug}.html").write_text(page_shell(title, guide["description"], url, body), encoding="utf-8")
        cards.append(f'      <li><a href="/guides/{slug}.html">{html.escape(title)}</a></li>')
        metadata.append({"slug": slug, "title": title, "url": url})
    index_url = f"{BASE_URL}/guides/index.html"
    urls.append(index_url)
    body = f"""    <article>
      <h1>Daanaa Giving Guides</h1>
      <p>These guides help donors, volunteers, nonprofit operators, and civic partners use public nonprofit information with care.</p>
{filterable_directory("guide-directory", "Filter giving guides", "Search giving guides", chr(10).join(cards))}
    </article>"""
    (out / "index.html").write_text(page_shell("Daanaa Giving Guides", "Guides for giving, volunteering, nonprofit discovery, and public data stewardship.", index_url, body), encoding="utf-8")
    return metadata


def write_sitemap(urls: list[str]) -> None:
    today = date.today().isoformat()
    path = PUBLIC / "growth-pages.xml"
    with path.open("w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for loc in sorted(set(urls)):
            f.write("  <url>\n")
            f.write(f"    <loc>{html.escape(loc, quote=True)}</loc>\n")
            f.write(f"    <lastmod>{today}</lastmod>\n")
            f.write("  </url>\n")
        f.write("</urlset>\n")


def write_outreach_kit(state_meta: list[dict[str, object]], category_meta: list[dict[str, object]], guide_meta: list[dict[str, object]], urls: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    top_states = state_meta[:10]
    top_categories = category_meta[:10]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rotation_month": ROTATION_MONTH,
        "next_refresh": NEXT_REFRESH,
        "public_growth_urls": len(set(urls)),
        "top_states": top_states,
        "top_categories": top_categories,
        "guides": guide_meta,
        "outreach_angles": [
            "State nonprofit associations can share state directory pages with members preparing to claim or improve profiles.",
            "Volunteer centers can link to giving and volunteer guides without endorsing specific nonprofits.",
            "Community foundations and managed funds can use Daanaa pages as public-context starting points, not recommendation lists.",
            "University nonprofit programs can use the open data and guides for public nonprofit discovery literacy.",
        ],
    }
    (REPORTS / "growth-pages.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        "# Growth Pages And Outreach Kit",
        "",
        f"Generated: {payload['generated_at']}",
        f"Rotation month: {payload['rotation_month']}",
        f"Next scheduled refresh: {payload['next_refresh']}",
        f"Public growth URLs: {payload['public_growth_urls']}",
        "",
        "## Outreach Positioning",
        "",
        "Daanaa has published public nonprofit discovery pages that help donors, volunteers, nonprofit operators, civic partners, search engines, and AI tools find nonprofit profiles by state, cause category, and giving intent.",
        "",
        "Use this language carefully: these pages are discovery maps, not rankings, endorsements, or paid placements. State and category pages highlight monthly hidden-gem sample profiles where available so smaller, lower-profile organizations are not crowded out by better-known institutions. Samples prioritize recent public financial context, use a $10,000 reported-revenue floor, and rotate monthly for broader exposure.",
        "",
        "## Sample Backlink Email",
        "",
        "Subject: Public nonprofit discovery pages for your community",
        "",
        "Hello,",
        "",
        "Daanaa has published public nonprofit discovery pages to help people find nonprofit profiles by state and cause category. The pages are generated from public-source-derived nonprofit data and are designed as discovery starting points, not rankings or endorsements.",
        "",
        "If useful for your members or community, you can link to the relevant state, category, or giving guide page. Nonprofits can also use Daanaa's claim path as the beta expands to improve public context for donors and volunteers.",
        "",
        "Daanaa is free for nonprofits, does not process donations or hold donor funds, and does not sell nonprofit visibility.",
        "",
        "## Top State Pages",
        "",
    ]
    md.extend(f"- [{item['name']}]({item['url']}): {item['count']:,} records" for item in top_states)
    md += ["", "## Top Category Pages", ""]
    md.extend(f"- [{item['name']}]({item['url']}): {item['count']:,} records" for item in top_categories)
    md += ["", "## Giving Guides", ""]
    md.extend(f"- [{item['title']}]({item['url']})" for item in guide_meta)
    (REPORTS / "growth-pages-outreach-kit.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    urls: list[str] = []
    with open_readonly() as conn:
        state_meta = write_state_pages(conn, urls)
        category_meta = write_category_pages(conn, urls)
    guide_meta = write_guides(urls)
    write_sitemap(urls)
    write_outreach_kit(state_meta, category_meta, guide_meta, urls)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rotation_month": ROTATION_MONTH,
        "next_refresh": NEXT_REFRESH,
        "url_count": len(set(urls)),
        "sitemap": f"{BASE_URL}/growth-pages.xml",
        "state_pages": len(state_meta),
        "category_pages": len(category_meta),
        "guide_pages": len(guide_meta),
    }
    (PUBLIC / "growth-pages-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {manifest['url_count']} growth URLs")
    print(f"State pages: {manifest['state_pages']}")
    print(f"Category pages: {manifest['category_pages']}")
    print(f"Guide pages: {manifest['guide_pages']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
