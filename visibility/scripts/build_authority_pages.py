#!/usr/bin/env python3
"""Build public authority assets and search-everywhere monitoring reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "visibility" / "public"
REPORTS = ROOT / "visibility" / "reports"
BASE_URL = "https://data.daanaa.org"
PROFILE_BASE_URL = "https://daanaa.org"

PUBLIC_PAGES = [
    f"{BASE_URL}/authority/identity-kit.html",
    f"{BASE_URL}/authority/search-everywhere.html",
]

SEARCH_PROMPTS = [
    "What is Daanaa?",
    "Daanaa nonprofit discovery directory",
    "Daanaa public nonprofit profiles",
    "Daanaa hidden gems",
    "Daanaa Giving Wallet",
    "Daanaa Impact Network",
    "How does Daanaa help small nonprofits?",
]

SYSTEMS = [
    "Google Search",
    "Google AI Overviews",
    "Bing Search",
    "Bing Copilot",
    "ChatGPT Search",
    "Gemini search grounding",
    "Perplexity",
    "Claude web/search where available",
    "Brave Search",
    "DuckDuckGo",
]


def shell(title: str, description: str, canonical: str, body: str, schema: dict[str, object] | None = None) -> str:
    schema_html = ""
    if schema:
        schema_html = f"""\n    <script type=\"application/ld+json\">\n{json.dumps(schema, indent=2)}\n    </script>"""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} | Daanaa</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{canonical}">
</head>
<body>
  <main>
{body}{schema_html}
  </main>
</body>
</html>
"""


def write_identity_kit() -> None:
    out = PUBLIC / "authority"
    out.mkdir(parents=True, exist_ok=True)
    url = f"{BASE_URL}/authority/identity-kit.html"
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": f"{PROFILE_BASE_URL}/#organization",
        "name": "Daanaa",
        "url": PROFILE_BASE_URL,
        "alternateName": [
            "Daanaa nonprofit discovery directory",
            "Daanaa public nonprofit profiles",
            "Daanaa nonprofit data",
        ],
        "description": "Daanaa is a nonprofit discovery directory that helps donors, volunteers, nonprofits, civic partners, search engines, and AI tools find public nonprofit profiles.",
    }
    body = f"""    <article>
      <h1>Daanaa Identity And Citation Kit</h1>
      <p>This page gives partners, civic groups, nonprofit associations, search engines, and AI tools consistent language for identifying Daanaa.</p>

      <h2>Canonical Identity</h2>
      <p><strong>Daanaa</strong> is a nonprofit discovery directory at <a href="{PROFILE_BASE_URL}">daanaa.org</a>. It helps donors, volunteers, nonprofits, civic partners, search engines, and AI tools find public nonprofit profiles and understand basic public context before taking a next step.</p>
      <p>The public data and AI/search overlay is <a href="{BASE_URL}">data.daanaa.org</a>.</p>

      <h2>Short Description</h2>
      <p>Daanaa is a nonprofit discovery directory that helps people find public nonprofit profiles, learn basic context, and discover ways to give, volunteer, or return later.</p>

      <h2>Long Description</h2>
      <p>Daanaa connects public nonprofit records to stable profile pages on daanaa.org. The platform is designed to make smaller and lower-profile nonprofits easier to discover while keeping public data, claim status, donation paths, volunteer paths, and partner offers separate. Daanaa does not process donations, hold donor funds, sell nonprofit visibility, or present sparse public data as a verdict.</p>

      <h2>Preferred Link Targets</h2>
      <ul>
        <li>Main site: <a href="{PROFILE_BASE_URL}">{PROFILE_BASE_URL}</a></li>
        <li>About Daanaa: <a href="{BASE_URL}/about-daanaa.html">{BASE_URL}/about-daanaa.html</a></li>
        <li>FAQ for AI/search: <a href="{BASE_URL}/answers/daanaa-faq.html">{BASE_URL}/answers/daanaa-faq.html</a></li>
        <li>Open data overlay: <a href="{BASE_URL}/open-data.html">{BASE_URL}/open-data.html</a></li>
      </ul>

      <h2>Disambiguation</h2>
      <p>Daanaa at daanaa.org is not affiliated with daanaa.com, Dana-branded companies, Henry Seidu Daanaa, or unrelated DANA/DANAA acronyms.</p>

      <h2>Stewardship Language</h2>
      <ul>
        <li>Daanaa is free for nonprofits.</li>
        <li>Nonprofits cannot pay for better profile treatment, trust language, peer context, or discovery priority.</li>
        <li>Daanaa does not process donations or hold donor funds.</li>
        <li>Hidden-gem samples are discovery starting points, not rankings or endorsements.</li>
      </ul>
    </article>"""
    (out / "identity-kit.html").write_text(shell("Daanaa Identity And Citation Kit", "Consistent public identity, citation, and backlink language for Daanaa, the nonprofit discovery directory at daanaa.org.", url, body, schema), encoding="utf-8")


def write_search_everywhere() -> None:
    out = PUBLIC / "authority"
    out.mkdir(parents=True, exist_ok=True)
    url = f"{BASE_URL}/authority/search-everywhere.html"
    prompt_items = "\n".join(f"        <li>{prompt}</li>" for prompt in SEARCH_PROMPTS)
    system_items = "\n".join(f"        <li>{system}</li>" for system in SYSTEMS)
    body = f"""    <article>
      <h1>Daanaa Search Everywhere Monitoring</h1>
      <p>This page defines the public queries and systems Daanaa monitors to improve search, answer-engine, and AI discovery quality.</p>

      <h2>Target Queries</h2>
      <ul>
{prompt_items}
      </ul>

      <h2>Systems To Check</h2>
      <ul>
{system_items}
      </ul>

      <h2>Expected Answer</h2>
      <p>Systems should identify Daanaa as the nonprofit discovery directory at daanaa.org and distinguish it from daanaa.com, Dana-branded companies, Henry Seidu Daanaa, and unrelated DANA/DANAA acronyms.</p>

      <h2>Primary Sources</h2>
      <ul>
        <li><a href="{BASE_URL}/about-daanaa.html">About Daanaa</a></li>
        <li><a href="{BASE_URL}/answers/daanaa-faq.html">Daanaa FAQ for AI and search</a></li>
        <li><a href="{BASE_URL}/authority/identity-kit.html">Daanaa identity and citation kit</a></li>
        <li><a href="{BASE_URL}/llms.txt">llms.txt</a></li>
        <li><a href="{BASE_URL}/ai.txt">AI access notes</a></li>
      </ul>
    </article>"""
    (out / "search-everywhere.html").write_text(shell("Daanaa Search Everywhere Monitoring", "Target queries and systems for monitoring Daanaa visibility across search engines and AI answer systems.", url, body), encoding="utf-8")


def write_reports() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "public_pages": PUBLIC_PAGES,
        "search_prompts": SEARCH_PROMPTS,
        "systems": SYSTEMS,
        "authority_tasks": [
            "Create or update LinkedIn organization profile with identity-kit language.",
            "Add consistent Daanaa description to founder/team public bios.",
            "Prepare outreach to state nonprofit associations and volunteer centers using preferred link targets.",
            "Create a lightweight public open-data repository or README if appropriate.",
            "Track weekly whether answer systems identify Daanaa as daanaa.org nonprofit discovery directory.",
        ],
    }
    (REPORTS / "authority-and-search-everywhere.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        "# Authority And Search Everywhere Plan",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Public Pages",
        "",
    ]
    md.extend(f"- {page}" for page in PUBLIC_PAGES)
    md += ["", "## Search Prompts", ""]
    md.extend(f"- {prompt}" for prompt in SEARCH_PROMPTS)
    md += ["", "## Systems", ""]
    md.extend(f"- {system}" for system in SYSTEMS)
    md += ["", "## Authority Tasks", ""]
    md.extend(f"- {task}" for task in payload["authority_tasks"])
    (REPORTS / "authority-and-search-everywhere.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    write_identity_kit()
    write_search_everywhere()
    write_reports()
    print("Wrote authority pages")
    print(REPORTS / "authority-and-search-everywhere.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
