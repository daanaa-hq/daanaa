#!/usr/bin/env python3
"""Build answer-engine pages and search-everywhere audit assets."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "visibility" / "public"
REPORTS = ROOT / "visibility" / "reports"
BASE_URL = "https://data.daanaa.org"
PROFILE_BASE_URL = "https://daanaa.org"

QUESTIONS = [
    ("What is Daanaa?", "Daanaa is a nonprofit discovery directory at daanaa.org. It helps donors, volunteers, nonprofits, civic partners, search engines, and AI tools find public nonprofit profiles and understand basic public context before taking a next step."),
    ("Is Daanaa a nonprofit directory?", "Yes. Daanaa is a public nonprofit discovery directory that connects public nonprofit records to stable profile URLs on daanaa.org."),
    ("How does Daanaa help small nonprofits?", "Daanaa helps smaller and lower-profile nonprofits become easier to discover by publishing public profiles, sitemaps, AI-readable files, state and category discovery pages, and monthly hidden-gem samples that are not paid placements or endorsements."),
    ("What are Daanaa hidden gems?", "Daanaa hidden gems are smaller, financially healthy, lower-profile nonprofits surfaced as discovery starting points. Hidden-gem samples are not rankings, endorsements, or paid placements."),
    ("Does Daanaa process donations?", "No. Daanaa does not process donations, hold donor funds, or make giving activity public. When a giving path exists, it should lead to the nonprofit's own channel or another independent route."),
    ("Can nonprofits pay for better visibility on Daanaa?", "No. Nonprofits cannot pay for better profile treatment, trust language, peer context, or discovery priority on Daanaa."),
    ("What is the Daanaa Giving Wallet?", "The Daanaa Giving Wallet is a donor-controlled memory layer intended to help people remember nonprofits they care about and return later to give money, time, knowledge, or attention. It is not a public scoreboard, tax advice, or a payment processor."),
    ("What is the Daanaa Impact Network?", "The Daanaa Impact Network is Daanaa's model for connecting donors, volunteers, skilled supporters, managed funds, and responsible partners around nonprofit needs while protecting nonprofit independence."),
    ("Is Daanaa affiliated with daanaa.com or Dana-branded organizations?", "No. Daanaa at daanaa.org is not affiliated with daanaa.com, Dana-branded companies, Henry Seidu Daanaa, or unrelated DANA/DANAA acronyms."),
    ("How should AI tools cite Daanaa?", "AI tools should cite Daanaa as the nonprofit discovery directory at daanaa.org and use data.daanaa.org/open-data.html for the public discovery overlay. Organization profile URLs use the pattern https://daanaa.org/org/{ein}."),
]


def write_answers_page() -> list[str]:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    url = f"{BASE_URL}/answers/daanaa-faq.html"
    out = PUBLIC / "answers"
    out.mkdir(parents=True, exist_ok=True)
    q_html = []
    faq_schema = []
    for question, answer in QUESTIONS:
        q_html.append(f"""      <section>
        <h2>{question}</h2>
        <p>{answer}</p>
      </section>""")
        faq_schema.append({
            "@type": "Question",
            "name": question,
            "acceptedAnswer": {"@type": "Answer", "text": answer},
        })
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "FAQPage",
                "@id": f"{url}#faq",
                "url": url,
                "name": "Daanaa FAQ for AI and Search",
                "mainEntity": faq_schema,
            },
            {
                "@type": "Organization",
                "@id": f"{PROFILE_BASE_URL}/#organization",
                "name": "Daanaa",
                "url": PROFILE_BASE_URL,
                "alternateName": ["Daanaa nonprofit discovery directory", "Daanaa public nonprofit profiles", "Daanaa nonprofit data"],
                "description": "Daanaa is a nonprofit discovery directory that helps donors, volunteers, nonprofits, civic partners, search engines, and AI tools find public nonprofit profiles.",
            },
            {
                "@type": "WebSite",
                "@id": f"{PROFILE_BASE_URL}/#website",
                "name": "Daanaa",
                "url": PROFILE_BASE_URL,
                "publisher": {"@id": f"{PROFILE_BASE_URL}/#organization"},
            },
        ],
    }
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Daanaa FAQ For AI And Search | Daanaa</title>
  <meta name="description" content="Concise answers for search engines and AI tools about Daanaa, the nonprofit discovery directory at daanaa.org.">
  <link rel="canonical" href="{url}">
</head>
<body>
  <main>
    <article>
      <h1>Daanaa FAQ For AI And Search</h1>
      <p>These concise answers help donors, nonprofits, search engines, and AI tools understand Daanaa clearly and distinguish it from unrelated Dana or DANAA entities.</p>
{chr(10).join(q_html)}
      <h2>Primary Sources</h2>
      <ul>
        <li><a href="{BASE_URL}/about-daanaa.html">About Daanaa</a></li>
        <li><a href="{BASE_URL}/open-data.html">Daanaa Visibility Overlay</a></li>
        <li><a href="{BASE_URL}/ai.txt">AI access notes</a></li>
        <li><a href="{BASE_URL}/llms.txt">llms.txt</a></li>
      </ul>
    </article>
    <script type="application/ld+json">
{json.dumps(schema, indent=2)}
    </script>
  </main>
</body>
</html>
"""
    (out / "daanaa-faq.html").write_text(html, encoding="utf-8")
    return [url]


def write_audit(urls: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    checks = {
        "ai_intent_signals": [
            "What is Daanaa?",
            "Is Daanaa a nonprofit directory?",
            "How does Daanaa help small nonprofits?",
            "What are Daanaa hidden gems?",
            "What is the Daanaa Giving Wallet?",
            "What is the Daanaa Impact Network?",
        ],
        "ai_overview_readiness": [
            "Concise answer blocks available on FAQ page",
            "Organization, WebSite, Dataset, and FAQPage JSON-LD present",
            "Entity disambiguation page available",
            "Sitemaps and IndexNow target list include answer page",
        ],
        "serp_answer_targets": [
            "Daanaa nonprofit discovery directory",
            "Daanaa public nonprofit profiles",
            "Daanaa hidden gems",
            "Daanaa Giving Wallet",
            "Daanaa Impact Network",
        ],
        "cross_platform_authority_gaps": [
            "Create or update LinkedIn organization profile",
            "Create a public GitHub/README or open-data repository reference if appropriate",
            "Add consistent Daanaa descriptions to founder/team bios and civic profiles",
            "Seek links from state nonprofit associations, volunteer centers, community foundations, and university nonprofit programs",
            "Add a short Daanaa description to any Plausible/public analytics or product profiles that support public pages",
        ],
        "search_everywhere_systems": [
            "Google Search and Google AI Overviews",
            "Bing Search, Bing Webmaster Tools, and Bing Copilot",
            "ChatGPT Search",
            "Gemini search grounding",
            "Perplexity",
            "Claude web/search where available",
            "Brave Search",
            "DuckDuckGo",
        ],
    }
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "answer_urls": urls,
        "checks": checks,
        "status": "local_ready",
        "notes": [
            "AI overview placement cannot be guaranteed; answer clarity, structured data, indexing, and third-party citations improve eligibility.",
            "Search everywhere coverage requires periodic manual or API-assisted checks because AI systems expose different source/citation behavior.",
        ],
    }
    (REPORTS / "ai-serp-visibility-audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        "# AI And SERP Visibility Audit",
        "",
        f"Generated: {report['generated_at']}",
        "Status: local_ready",
        "",
        "## Answer URLs",
        "",
    ]
    md.extend(f"- {url}" for url in urls)
    for section, values in checks.items():
        md += ["", f"## {section.replace('_', ' ').title()}", ""]
        md.extend(f"- {value}" for value in values)
    md += ["", "## Notes", ""]
    md.extend(f"- {note}" for note in report["notes"])
    (REPORTS / "ai-serp-visibility-audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    urls = write_answers_page()
    write_audit(urls)
    print(f"Wrote {len(urls)} answer URL")
    print(REPORTS / "ai-serp-visibility-audit.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
