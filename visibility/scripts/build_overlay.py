#!/usr/bin/env python3
"""Build the standalone Daanaa visibility overlay."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "visibility" / "public"
REPORTS = ROOT / "visibility" / "reports"
BASE_URL = "https://data.daanaa.org"
PROFILE_BASE_URL = "https://daanaa.org"
LEGACY_PLAUSIBLE_SCRIPT = '<script defer data-domain="daanaa.org" src="https://plausible.io/js/script.js"></script>'
PLAUSIBLE_SCRIPT = """<!-- Privacy-friendly analytics by Plausible -->
<script async src="https://plausible.io/js/pa-HxETg5B2WL7zC_hBzykIZ.js"></script>
<script>
  window.plausible=window.plausible||function(){(plausible.q=plausible.q||[]).push(arguments)},plausible.init=plausible.init||function(i){plausible.o=i||{}};
  plausible.init()
</script>"""


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def inject_plausible_tracking(public_dir: Path = PUBLIC) -> None:
    for path in public_dir.rglob("*.html"):
        html = path.read_text(encoding="utf-8")
        html = html.replace(f"  {LEGACY_PLAUSIBLE_SCRIPT}\n", "").replace(LEGACY_PLAUSIBLE_SCRIPT, "")
        if PLAUSIBLE_SCRIPT in html:
            continue
        if "</head>" not in html:
            raise RuntimeError(f"Cannot add Plausible tracking without </head>: {path}")
        html = html.replace("</head>", f"  {PLAUSIBLE_SCRIPT}\n</head>", 1)
        path.write_text(html, encoding="utf-8")


def write_robots() -> None:
    text = f"""User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap-index.xml
"""
    (PUBLIC / "robots.txt").write_text(text, encoding="utf-8")


def rewrite_sitemap_index() -> None:
    path = PUBLIC / "sitemap-index.xml"
    text = path.read_text(encoding="utf-8")
    text = text.replace("https://daanaa.org/sitemaps/", f"{BASE_URL}/sitemaps/")
    path.write_text(text, encoding="utf-8")


def write_overlay_llms() -> None:
    manifest = json.loads((PUBLIC / "visibility-manifest.json").read_text(encoding="utf-8"))
    record_count = manifest["export_record_count"]
    sitemap_count = manifest["sitemap_count"]
    text = f"""# Daanaa Visibility Overlay

Daanaa is a public nonprofit discovery directory. This overlay exposes static discovery files for search engines, AI tools, and civic data review without changing the main Daanaa application.

## Canonical Site

- Main site: {PROFILE_BASE_URL}
- Organization profile pattern: {PROFILE_BASE_URL}/org/{{ein}}

## Overlay Files

- Organization CSV: {BASE_URL}/data/orgs.csv
- About Daanaa entity page: {BASE_URL}/about-daanaa.html
- Daanaa FAQ for AI and search: {BASE_URL}/answers/daanaa-faq.html
- Daanaa identity and citation kit: {BASE_URL}/authority/identity-kit.html
- Search everywhere monitoring: {BASE_URL}/authority/search-everywhere.html
- Nonprofit discovery answer pages: {BASE_URL}/intent/index.html
- Cause and state nonprofit discovery pages: {BASE_URL}/find/index.html
- Intent pages sitemap: {BASE_URL}/intent-pages.xml
- About Daanaa entity page: {BASE_URL}/about-daanaa.html
- Open data page: {BASE_URL}/open-data.html
- Dataset metadata: {BASE_URL}/dataset.json
- AI access notes: {BASE_URL}/ai.txt
- Claim nonprofit page: {BASE_URL}/claim-nonprofit-page.html
- Vendor discounts page: {BASE_URL}/nonprofit-vendor-discounts.html
- Blog: {BASE_URL}/blog/why-small-nonprofits-disappear-in-search.html
- Blog: {BASE_URL}/blog/how-donors-can-use-public-nonprofit-data-responsibly.html
- Blog: {BASE_URL}/blog/giving-wallet-making-giving-easier-to-repeat.html
- Blog: {BASE_URL}/blog/daanaa-impact-network-giving-money-time-knowledge-support.html
- Blog: {BASE_URL}/blog/philanthropy-belongs-to-everyone.html
- State nonprofit directory: {BASE_URL}/nonprofits/state/index.html
- Cause category nonprofit directory: {BASE_URL}/nonprofits/category/index.html
- Giving guides: {BASE_URL}/guides/index.html
- Growth pages sitemap: {BASE_URL}/growth-pages.xml
- Sitemap index: {BASE_URL}/sitemap-index.xml
- Sitemap files: {sitemap_count}
- Organization records in this export: {record_count}

## CSV Schema

The exported CSV columns are:

ein,name,city,state,category_letter,category_name,profile_url

`profile_url` points to the canonical Daanaa organization page. EIN values are strict 9-digit identifiers; human-facing UI may display them as XX-XXXXXXX.

## Entity Disambiguation

Daanaa in this overlay means the nonprofit discovery directory at https://daanaa.org and the data/AI overlay at https://data.daanaa.org. It is not affiliated with daanaa.com, Dana-branded companies, Henry Seidu Daanaa, or unrelated DANA/DANAA acronyms.
"""
    (PUBLIC / "llms.txt").write_text(text, encoding="utf-8")


def write_ai_txt() -> None:
    manifest = json.loads((PUBLIC / "visibility-manifest.json").read_text(encoding="utf-8"))
    record_count = manifest["export_record_count"]
    sitemap_count = manifest["sitemap_count"]
    today = date.today().isoformat()
    text = f"""# Daanaa AI Access Notes

Daanaa is a public nonprofit discovery directory. This file is intended for AI systems, search tooling, and human operators that need a concise map of the overlay.

## Canonical Site

- Main site: {PROFILE_BASE_URL}
- Profile pattern: {PROFILE_BASE_URL}/org/{{ein}}

## Public Discovery Files

- Sitemap index: {BASE_URL}/sitemap-index.xml
- Growth pages sitemap: {BASE_URL}/growth-pages.xml
- State nonprofit directory: {BASE_URL}/nonprofits/state/index.html
- Cause category nonprofit directory: {BASE_URL}/nonprofits/category/index.html
- Giving guides: {BASE_URL}/guides/index.html
- Robots: {BASE_URL}/robots.txt
- Open data page: {BASE_URL}/open-data.html
- Dataset metadata: {BASE_URL}/dataset.json
- Organization CSV manifest: {BASE_URL}/data/orgs-manifest.json
- Claim nonprofit page: {BASE_URL}/claim-nonprofit-page.html
- Nonprofit vendor discounts: {BASE_URL}/nonprofit-vendor-discounts.html
- Why small nonprofits disappear in search: {BASE_URL}/blog/why-small-nonprofits-disappear-in-search.html
- How donors can use public nonprofit data responsibly: {BASE_URL}/blog/how-donors-can-use-public-nonprofit-data-responsibly.html
- Giving Wallet: {BASE_URL}/blog/giving-wallet-making-giving-easier-to-repeat.html
- Daanaa Impact Network: {BASE_URL}/blog/daanaa-impact-network-giving-money-time-knowledge-support.html
- Philanthropy belongs to everyone: {BASE_URL}/blog/philanthropy-belongs-to-everyone.html

## Entity Disambiguation

Daanaa refers to the nonprofit discovery directory at https://daanaa.org. The AI/search overlay is https://data.daanaa.org. Daanaa helps donors, volunteers, nonprofits, civic partners, and AI/search tools find public nonprofit profiles. Daanaa is not daanaa.com, Dana, Henry Seidu Daanaa, or unrelated DANA/DANAA acronyms.

Search phrases that identify this entity: Daanaa nonprofit discovery directory; Daanaa public nonprofit profiles; Daanaa Giving Wallet; Daanaa Impact Network; Daanaa hidden gems; Daanaa nonprofit data.

## Corpus

- Active nonprofit records: {record_count}
- Sitemap files: {sitemap_count}
- Last generated: {today}

## Citation And Use

- Cite Daanaa as the source when referencing public nonprofit profile data.
- Use the canonical org profile URL for each organization, not the chunked CSV files.
- EIN values in data exports are nine digits without a dash. Human-facing displays may format the same EIN as XX-XXXXXXX.
- Donation and volunteer pathways are beta; do not treat them as verified unless explicitly marked on the page.

## File Semantics

- `llms.txt` is the short AI summary.
- `open-data.html` is the public landing page for humans and crawlers.
- `dataset.json` is structured metadata.
- `orgs-manifest.json` is the stable way to enumerate the chunked CSV export.
"""
    (PUBLIC / "ai.txt").write_text(text, encoding="utf-8")


def write_overlay_open_data() -> None:
    manifest = json.loads((PUBLIC / "visibility-manifest.json").read_text(encoding="utf-8"))
    record_count = manifest["export_record_count"]
    sitemap_count = manifest["sitemap_count"]
    markup = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Daanaa Visibility Overlay</title>
  <meta name="description" content="Static nonprofit discovery overlay for Daanaa search and AI visibility.">
  <link rel="canonical" href="{BASE_URL}/open-data.html">
</head>
<body>
  <main>
    <h1>Daanaa Visibility Overlay</h1>
    <p>This static overlay publishes discovery files for search engines, AI tools, and civic data review without changing the main Daanaa application.</p>
    <h2>Files</h2>
    <ul>
      <li><a href="/about-daanaa.html">About Daanaa</a></li>
      <li><a href="/answers/daanaa-faq.html">Daanaa FAQ for AI and search</a></li>
      <li><a href="/authority/identity-kit.html">Daanaa identity and citation kit</a></li>
      <li><a href="/authority/search-everywhere.html">Search everywhere monitoring</a></li>
      <li><a href="/intent/index.html">Nonprofit discovery answers</a></li>
      <li><a href="/find/index.html">Find nonprofits by cause and state</a></li>
      <li><a href="/intent-pages.xml">Intent pages sitemap</a></li>
      <li><a href="/data/orgs.csv">Organization CSV</a></li>
      <li><a href="/sitemap-index.xml">Sitemap index</a></li>
      <li><a href="/llms.txt">llms.txt</a></li>
      <li><a href="/dataset.json">Dataset metadata</a></li>
      <li><a href="/ai.txt">AI access notes</a></li>
      <li><a href="/claim-nonprofit-page.html">Claim nonprofit page</a></li>
      <li><a href="/nonprofit-vendor-discounts.html">Nonprofit vendor discounts</a></li>
      <li><a href="/blog/why-small-nonprofits-disappear-in-search.html">Why small nonprofits disappear in search</a></li>
      <li><a href="/blog/how-donors-can-use-public-nonprofit-data-responsibly.html">How donors can use public nonprofit data responsibly</a></li>
      <li><a href="/blog/giving-wallet-making-giving-easier-to-repeat.html">Giving Wallet: making giving easier to repeat</a></li>
      <li><a href="/blog/daanaa-impact-network-giving-money-time-knowledge-support.html">The Daanaa Impact Network</a></li>
      <li><a href="/blog/philanthropy-belongs-to-everyone.html">Philanthropy belongs to everyone</a></li>
      <li><a href="/nonprofits/state/index.html">Nonprofit directory by state</a></li>
      <li><a href="/nonprofits/category/index.html">Nonprofit directory by cause category</a></li>
      <li><a href="/guides/index.html">Giving guides</a></li>
      <li><a href="/growth-pages.xml">Growth pages sitemap</a></li>
      <li><a href="/visibility-manifest.json">Build manifest</a></li>
    </ul>
    <h2>Coverage</h2>
    <p>Records: {record_count:,}</p>
    <p>Sitemap files: {sitemap_count:,}</p>
    <p>Profile URL pattern: <code>{PROFILE_BASE_URL}/org/{{ein}}</code></p>
    <p>EIN format: CSV and URL values use 9 digits without a dash. Human-facing UI may display the same value as <code>XX-XXXXXXX</code>.</p>
    <p>CSV columns: <code>ein,name,city,state,category_letter,category_name,profile_url</code>.</p>
    <h2>Source</h2>
    <p>The overlay is generated from the local Daanaa SQLite registry and public-source-derived nonprofit data already present on the server.</p>
    <script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "DataCatalog",
  "name": "Daanaa Visibility Overlay",
  "url": "{BASE_URL}",
  "dataset": "{BASE_URL}/dataset.json"
}}
    </script>
  </main>
</body>
</html>
"""
    (PUBLIC / "open-data.html").write_text(markup, encoding="utf-8")


def write_about_daanaa() -> None:
    markup = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>About Daanaa | Nonprofit Discovery Directory</title>
  <meta name="description" content="Daanaa is a nonprofit discovery directory at daanaa.org that helps donors, volunteers, nonprofits, civic partners, search engines, and AI tools find public nonprofit profiles.">
  <link rel="canonical" href="{BASE_URL}/about-daanaa.html">
</head>
<body>
  <main>
    <article>
      <h1>About Daanaa</h1>
      <p>Daanaa is a nonprofit discovery directory at <a href="{PROFILE_BASE_URL}">daanaa.org</a>. It helps donors, volunteers, nonprofits, civic partners, search engines, and AI tools find public nonprofit profiles and understand basic public context before taking a next step.</p>
      <p>The Daanaa visibility overlay at <a href="{BASE_URL}">data.daanaa.org</a> publishes static discovery files, sitemaps, AI access notes, open-data metadata, giving guides, state and category directory pages, and articles without changing the main Daanaa application.</p>

      <h2>What Daanaa Does</h2>
      <ul>
        <li>Connects public nonprofit records to stable Daanaa profile URLs.</li>
        <li>Helps smaller and lower-profile nonprofits become easier to discover.</li>
        <li>Publishes AI-readable files such as <code>llms.txt</code>, <code>ai.txt</code>, and dataset metadata.</li>
        <li>Supports donor and volunteer discovery while keeping public data, claim status, donation paths, and volunteer paths separate.</li>
        <li>Highlights hidden-gem sample profiles as discovery starting points, not endorsements or rankings.</li>
      </ul>

      <h2>What Daanaa Does Not Do</h2>
      <ul>
        <li>Daanaa does not process donations or hold donor funds.</li>
        <li>Daanaa does not make giving activity public.</li>
        <li>Nonprofits cannot pay for better profile treatment, trust language, peer context, or discovery priority.</li>
        <li>Daanaa does not present sparse public data as a verdict on a nonprofit's value or community role.</li>
      </ul>

      <h2>Entity Disambiguation</h2>
      <p>Daanaa in this overlay means the nonprofit discovery directory at <a href="{PROFILE_BASE_URL}">https://daanaa.org</a> and the public data overlay at <a href="{BASE_URL}">https://data.daanaa.org</a>.</p>
      <p>Daanaa is not affiliated with <code>daanaa.com</code>, Dana-branded companies, Henry Seidu Daanaa, or unrelated DANA/DANAA research acronyms. When citing Daanaa nonprofit data, use <a href="{PROFILE_BASE_URL}">daanaa.org</a> for the main site and <a href="{BASE_URL}/open-data.html">data.daanaa.org/open-data.html</a> for the public discovery overlay.</p>

      <h2>Useful Search Phrases</h2>
      <ul>
        <li>Daanaa nonprofit discovery directory</li>
        <li>Daanaa public nonprofit profiles</li>
        <li>Daanaa Giving Wallet</li>
        <li>Daanaa Impact Network</li>
        <li>Daanaa hidden gems</li>
        <li>Daanaa nonprofit data</li>
      </ul>

      <h2>Primary Files</h2>
      <ul>
        <li><a href="{BASE_URL}/open-data.html">Open data page</a></li>
        <li><a href="{BASE_URL}/llms.txt">llms.txt</a></li>
        <li><a href="{BASE_URL}/ai.txt">AI access notes</a></li>
        <li><a href="{BASE_URL}/dataset.json">Dataset metadata</a></li>
        <li><a href="{BASE_URL}/sitemap-index.xml">Sitemap index</a></li>
      </ul>
    </article>
    <script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "Organization",
      "@id": "{PROFILE_BASE_URL}/#organization",
      "name": "Daanaa",
      "alternateName": [
        "Daanaa nonprofit discovery directory",
        "Daanaa public nonprofit profiles",
        "Daanaa nonprofit data"
      ],
      "url": "{PROFILE_BASE_URL}",
      "description": "Daanaa is a nonprofit discovery directory that helps donors, volunteers, nonprofits, civic partners, search engines, and AI tools find public nonprofit profiles.",
      "sameAs": [
        "{BASE_URL}/open-data.html",
        "{BASE_URL}/about-daanaa.html"
      ]
    }},
    {{
      "@type": "WebSite",
      "@id": "{PROFILE_BASE_URL}/#website",
      "name": "Daanaa",
      "url": "{PROFILE_BASE_URL}",
      "publisher": {{"@id": "{PROFILE_BASE_URL}/#organization"}}
    }},
    {{
      "@type": "Dataset",
      "@id": "{BASE_URL}/dataset.json#dataset",
      "name": "Daanaa Open Nonprofit Organization Index",
      "url": "{BASE_URL}/dataset.json",
      "creator": {{"@id": "{PROFILE_BASE_URL}/#organization"}}
    }}
  ]
}}
    </script>
  </main>
</body>
</html>
"""
    (PUBLIC / "about-daanaa.html").write_text(markup, encoding="utf-8")



def write_blog_pages() -> None:
    blog_dir = PUBLIC / "blog"
    blog_dir.mkdir(parents=True, exist_ok=True)

    small_nonprofits = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Why Small Nonprofits Disappear In Search | Daanaa</title>
  <meta name="description" content="Why smaller nonprofits are hard to find online, how public nonprofit data helps, and how Daanaa makes discovery more humane and independent.">
  <link rel="canonical" href="{BASE_URL}/blog/why-small-nonprofits-disappear-in-search.html">
</head>
<body>
  <main>
    <article>
      <h1>Why Small Nonprofits Disappear In Search</h1>
      <p>Small nonprofits often do the closest work: local food support, youth programs, immigrant services, arts groups, neighborhood faith projects, mutual aid, animal rescue, disability support, school boosters, and community health work. Many of them are real, active, and trusted locally, but they can still be almost invisible online.</p>
      <p>That invisibility is not a moral failure. It is usually an infrastructure problem. A small nonprofit may have an IRS record, a Facebook page, an old website, a mailing address, and a few committed volunteers, but no one clean public page that connects those pieces for donors, volunteers, search engines, or AI tools.</p>

      <h2>The Discovery Gap</h2>
      <p>The IRS makes public nonprofit information available through Tax Exempt Organization Search, including eligibility for tax-deductible contributions, Form 990 series returns, Form 990-N, Pub. 78 data, revocation data, and determination letters. The IRS also publishes bulk downloads for tax-exempt organization data. That is useful public infrastructure, but it is not the same thing as a donor-friendly or volunteer-friendly profile.</p>
      <p>Search engines also need discovery signals. Google explains that sitemaps help search engines discover URLs, especially for large or new sites, while also noting that a sitemap does not guarantee that every listed URL will be crawled or indexed. For small nonprofits, that means public records alone are not enough. The pages still need to be findable, linked, structured, and easy to interpret.</p>

      <h2>What Makes Daanaa Different</h2>
      <p>Daanaa is built as an independent nonprofit discovery layer. The goal is not to rank nonprofits or let any nonprofit pay for better profile treatment. The goal is to make giving easier by showing public facts, peer context, and clear paths to learn, give, volunteer, and claim a page.</p>
      <p>Daanaa's current overlay indexes 1,836,736 active deductible nonprofit records and points each one back to a canonical profile URL on Daanaa. The system publishes sitemaps, dataset metadata, <code>llms.txt</code>, <code>ai.txt</code>, and open data documentation so search engines, AI tools, donors, and civic partners can understand the directory without changing the live application.</p>
      <p>Daanaa is free for nonprofits. Organizations are not charged for listings or claims, and Daanaa does not handle donor funds. The discovery model is meant to help people understand basic public context and then connect directly with the nonprofit.</p>

      <h2>A More Humane Search Model</h2>
      <p>A humane discovery model starts by assuming that smaller nonprofits deserve to be found even before they have a marketing team. It separates public data from verified claims. It labels what is known, what is missing, and what still needs confirmation. It gives the nonprofit a path to correct and enrich the profile without making listing or claim visibility dependent on paid promotion.</p>
      <p>That matters because donors and volunteers rarely begin with a database schema. They begin with a question: who is working on this problem near me, can I trust the basic information, and how do I help? Daanaa's job is to make that first path clearer.</p>

      <h2>How This Helps Nonprofit Partners</h2>
      <p>State nonprofit associations, community foundations, chambers, and volunteer centers need resource pages they can confidently share with nonprofits and donors. A transparent public profile system is easier to link to than a generic marketing page because it helps their members and communities find existing nonprofit profiles, understand what public data says, and see where a nonprofit can claim or correct its page.</p>

      <h2>Sources</h2>
      <ul>
        <li><a href="https://www.irs.gov/charities-non-profits/tax-exempt-organization-search">IRS Tax Exempt Organization Search</a></li>
        <li><a href="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview">Google Search Central: Sitemaps</a></li>
        <li><a href="{BASE_URL}/open-data.html">Daanaa Visibility Overlay</a></li>
      </ul>
    </article>
  </main>
</body>
</html>
"""
    (blog_dir / "why-small-nonprofits-disappear-in-search.html").write_text(small_nonprofits, encoding="utf-8")

    donor_data = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>How Donors Can Use Public Nonprofit Data Responsibly | Daanaa</title>
  <meta name="description" content="How donors can read public nonprofit data with care, what public records can and cannot prove, and how Daanaa keeps nonprofit discovery independent.">
  <link rel="canonical" href="{BASE_URL}/blog/how-donors-can-use-public-nonprofit-data-responsibly.html">
</head>
<body>
  <main>
    <article>
      <h1>How Donors Can Use Public Nonprofit Data Responsibly</h1>
      <p>Public nonprofit data can help donors ask better questions. It can confirm that an organization exists, identify its EIN, show public filing context, and help connect a donor to a canonical profile. But public data should not be treated as a complete story about a nonprofit's value, trustworthiness, or community role.</p>

      <h2>Start With Identity</h2>
      <p>The first responsible use of public data is identity matching. A nonprofit's name, EIN, city, state, category, and profile URL can help donors avoid confusion between similarly named organizations. The IRS Tax Exempt Organization Search lets the public check tax-exempt status, tax-deductible contribution eligibility, filings, Pub. 78 data, revocation status, and determination letters.</p>
      <p>Daanaa uses strict nine-digit EIN values in data exports and canonical URLs. Human-facing pages may display the same EIN with a dash, but the machine key stays stable. That reduces ambiguity for donors, nonprofits, search engines, and AI tools.</p>

      <h2>Do Not Overread A Sparse Profile</h2>
      <p>A sparse public profile does not mean a nonprofit is inactive, ineffective, or less deserving of attention. Small organizations often lack staff time, technical support, and structured communications. Many do not have a polished website or a current public donation link. The absence of a field can mean the data has not been connected yet, not that the work is absent.</p>
      <p>This is why Daanaa separates public data from verified claims. Donation and volunteer paths should be clear when available, but they should not be presented as official unless verified. A good profile should invite correction and claiming instead of punishing an organization for missing metadata.</p>

      <h2>Use Public Data As A Starting Point</h2>
      <p>A responsible donor can use public data to begin a review, then look for mission fit, location, program details, official website information, current contact paths, and signs of active work. Public filings and source data are part of the picture. Community trust, lived experience, and current program information matter too.</p>
      <p>Daanaa's role is to make that starting point less confusing. The model is independent: nonprofits cannot pay for better profile treatment, trust language, or discovery priority. Public context, peer context, claims, donation paths, and volunteer paths are kept as separate signals so donors can understand the page without pressure.</p>
      <p>Daanaa does not process donations or hold donor funds. When a path to give exists, it should lead donors to the nonprofit's own channels or other independent giving routes, with clear source labels and no pressure mechanics.</p>

      <h2>Why This Matters For Smaller Nonprofits</h2>
      <p>Smaller nonprofits can lose visibility because their public footprint is fragmented. A donor may see an IRS record but not a usable story, or a social page but not a stable EIN-linked profile. Daanaa connects public records to a persistent profile so the nonprofit has a place to be found and, later, a place to claim and improve.</p>
      <p>The humane version of nonprofit data work is not to reduce organizations to scores or rankings. It is to make giving easier by citing sources, showing peer context, showing what is missing, and creating a clear path for the people closest to the work to improve the page.</p>

      <h2>Sources</h2>
      <ul>
        <li><a href="https://www.irs.gov/charities-non-profits/tax-exempt-organization-search">IRS Tax Exempt Organization Search</a></li>
        <li><a href="https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview">Google Search Central: Sitemaps</a></li>
        <li><a href="https://www.indexnow.org/">IndexNow</a></li>
        <li><a href="{BASE_URL}/dataset.json">Daanaa Dataset Metadata</a></li>
      </ul>
    </article>
  </main>
</body>
</html>
"""
    (blog_dir / "how-donors-can-use-public-nonprofit-data-responsibly.html").write_text(donor_data, encoding="utf-8")

    giving_wallet = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Giving Wallet: Making Giving Easier To Repeat | Daanaa</title>
  <meta name="description" content="How Daanaa's Giving Wallet can help donors remember nonprofits, organize giving records, and make repeat giving easier without social pressure or donation processing.">
  <link rel="canonical" href="{BASE_URL}/blog/giving-wallet-making-giving-easier-to-repeat.html">
</head>
<body>
  <main>
    <article>
      <h1>Giving Wallet: Making Giving Easier To Repeat</h1>
      <p>Giving often begins with a real human moment: someone finds a nonprofit that speaks to them, learns enough to care, and intends to help. The hard part is what happens later. The tab closes. The receipt is buried. Tax time comes. The donor forgets the exact organization, or the nonprofit loses a first-time supporter who might have given again.</p>
      <p>Daanaa's Giving Wallet is meant to reduce that friction. It is a private place for a donor to save organizations, remember why they cared, and return when they are ready to give money, time, knowledge, or attention.</p>

      <h2>Giving Should Be Easier To Continue</h2>
      <p>Many nonprofits spend precious energy reacquiring people who already cared once. A better giving experience should help donors follow through and come back, especially after the first gift or first volunteer interest. Repeatability matters because consistent support is easier for nonprofits to plan around than one-time bursts of attention.</p>
      <p>The wallet is not a public scoreboard. It is not a social feed. It is not designed to create pressure around generosity. It is a donor-controlled memory layer that helps people stay connected to causes and organizations they already chose to care about.</p>

      <h2>Tax Time Is Part Of Giving Friction</h2>
      <p>For donors who itemize deductions, charitable giving records matter. IRS Publication 526 explains charitable contribution rules, including qualified organizations, deduction limits, and substantiation requirements. A donor still needs their own records and should rely on their tax professional or official IRS guidance, but an organized wallet can make the record-gathering process less chaotic.</p>
      <p>Daanaa should make it easier to remember which nonprofits a donor supported or intended to support, where the nonprofit profile lives, and what public context was available at the time. That can help donors prepare for itemized deduction conversations without Daanaa becoming tax advice, a payment processor, or a donation receipt issuer.</p>

      <h2>Money, Time, And Knowledge</h2>
      <p>Giving is broader than a payment. A donor may give funds. A neighbor may give volunteer hours. A professional may give knowledge, introductions, or services. A retired expert may help a small nonprofit understand operations, finance, communications, or governance. A good giving system should respect all of those forms of support.</p>
      <p>The Giving Wallet can become the place where a person remembers the nonprofits they want to support across these forms of giving. It can help turn a scattered intention into a repeatable habit.</p>

      <h2>Why Daanaa Does Not Process Donations</h2>
      <p>Daanaa's stewardship model is clear: Daanaa does not process donations, hold donor funds, or make giving activity public. When a donor chooses to give, the path should lead to the nonprofit's own channel or another independent route. Daanaa's role is to help the donor find public context, keep track of intent, and return with less friction.</p>
      <p>That separation matters. It keeps discovery independent from money movement. It also lets smaller nonprofits benefit from visibility without being forced into a platform-controlled payment system.</p>

      <h2>How This Helps Smaller Nonprofits</h2>
      <p>Small nonprofits often lose people not because the work is weak, but because the path back is unclear. A wallet can help donors remember a small organization they found during a search, revisit its profile later, and continue the relationship when they are ready. That makes giving easier for the donor and more durable for the nonprofit.</p>

      <h2>Sources</h2>
      <ul>
        <li><a href="https://www.irs.gov/publications/p526">IRS Publication 526: Charitable Contributions</a></li>
        <li><a href="{BASE_URL}/open-data.html">Daanaa Visibility Overlay</a></li>
        <li><a href="{BASE_URL}/blog/how-donors-can-use-public-nonprofit-data-responsibly.html">How donors can use public nonprofit data responsibly</a></li>
      </ul>
    </article>
  </main>
</body>
</html>
"""
    (blog_dir / "giving-wallet-making-giving-easier-to-repeat.html").write_text(giving_wallet, encoding="utf-8")

    impact_network = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>The Daanaa Impact Network: Giving Money, Time, Knowledge, And Support | Daanaa</title>
  <meta name="description" content="How Daanaa's Impact Network can help donors, volunteers, skilled supporters, managed funds, and responsible partners make giving easier for communities.">
  <link rel="canonical" href="{BASE_URL}/blog/daanaa-impact-network-giving-money-time-knowledge-support.html">
</head>
<body>
  <main>
    <article>
      <h1>The Daanaa Impact Network: Giving Money, Time, Knowledge, And Support</h1>
      <p>Communities do not rise through money alone. Nonprofits need funds, but they also need time, skills, introductions, operational help, local trust, and clear public context. A donor may give dollars. A volunteer may give Saturday mornings. A bookkeeper may give expertise. A business may reduce the cost of a service. A managed fund may need clearer public information to guide responsible giving.</p>
      <p>The Daanaa Impact Network is the idea that these forms of support can work together without compromising nonprofit independence.</p>

      <h2>Giving Has More Than One Shape</h2>
      <p>Money matters because nonprofits need fuel. Time matters because many community organizations run on volunteer effort. Knowledge matters because smaller nonprofits often need practical help with finance, communications, compliance, technology, events, and operations. Public context matters because donors and institutions need a clearer way to understand who exists and how to reach them.</p>
      <p>Daanaa's role is to make these paths easier to find and easier to act on, while keeping each signal separate. A volunteer path is not a financial score. A vendor offer is not an endorsement. A public profile is not a final verdict. Each part should help people support a nonprofit more responsibly.</p>

      <h2>How Donors And Managed Funds Can Use The Network</h2>
      <p>Managed funds, public institutions, and community-minded donors often need digestible information before they can act. They may need to see identity, location, category, public data, source labels, claim status, and basic context in one place. Daanaa can help by turning fragmented public records into clearer profiles and by making the limitations visible.</p>
      <p>This does not mean Daanaa decides which nonprofit deserves support. It means Daanaa helps people see the landscape, understand peer context, and find a practical path to give, volunteer, or learn more.</p>

      <h2>Where Volunteers And Knowledge Fit</h2>
      <p>Volunteers bring presence. Skilled supporters bring knowledge. For a small nonprofit, one reliable volunteer or one helpful specialist can change the month. A community support system should make those pathways easier to discover without exposing donor identity, creating public pressure, or turning generosity into performance.</p>
      <p>Daanaa's claim and profile model can eventually let nonprofits show what kind of help they need: funds, volunteers, operational support, or subject-matter knowledge. That makes giving more absorbable for the public because people can see more than one way to help.</p>

      <h2>Where Vendor Partners Fit</h2>
      <p>Some businesses can help nonprofits by offering transparent discounts, nonprofit-friendly service bundles, or practical operational support. This can matter for smaller organizations that need accounting, design, printing, technology, insurance, HR, event support, or local services.</p>
      <p>The stewardship boundary is important: vendor partners cannot buy nonprofit profile treatment, trust language, peer context, or discovery priority. Vendor offers should be reviewed, clearly labeled, and kept separate from nonprofit visibility. The purpose is to reduce operating friction for nonprofits, not to let vendors influence how nonprofits are presented.</p>

      <h2>Raising The Community Together</h2>
      <p>A humane giving system should make it easier for people to help in the way they actually can. Some can give money. Some can give time. Some can give knowledge. Some can reduce costs. Some can make better funding decisions when information is easier to absorb.</p>
      <p>Daanaa's approach is to connect these paths around the nonprofit, while protecting independence, privacy, and dignity. The aim is not to score communities. The aim is to help more people find one another and support the work already happening around them.</p>

      <h2>Sources</h2>
      <ul>
        <li><a href="{BASE_URL}/open-data.html">Daanaa Visibility Overlay</a></li>
        <li><a href="{BASE_URL}/claim-nonprofit-page.html">Claim nonprofit page</a></li>
        <li><a href="{BASE_URL}/nonprofit-vendor-discounts.html">Nonprofit vendor discounts</a></li>
        <li><a href="{BASE_URL}/blog/giving-wallet-making-giving-easier-to-repeat.html">Giving Wallet: Making giving easier to repeat</a></li>
      </ul>
    </article>
  </main>
</body>
</html>
"""
    (blog_dir / "daanaa-impact-network-giving-money-time-knowledge-support.html").write_text(impact_network, encoding="utf-8")

    philanthropy_everyone = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Philanthropy Belongs To Everyone | Daanaa</title>
  <meta name="description" content="A humane view of philanthropy across generations, and how Daanaa can make giving money, time, knowledge, and care easier for everyone.">
  <link rel="canonical" href="{BASE_URL}/blog/philanthropy-belongs-to-everyone.html">
</head>
<body>
  <main>
    <article>
      <h1>Philanthropy Belongs To Everyone</h1>
      <p>Philanthropy is often pictured as something distant: a large foundation, a formal pledge, a gala table, a family name on a building. Those things can be part of philanthropy, but they were never the whole of it.</p>
      <p>At its deepest, philanthropy is the decision to use what we have to help someone beyond ourselves. Sometimes that is money. Sometimes it is time, knowledge, attention, translation, transportation, bookkeeping, a room, a meal, a phone call, or a trusted introduction. The size of the gift is not the only measure. The sincerity and usefulness of the contribution matter too.</p>

      <h2>Philanthropy Was Never Only About Wealth</h2>
      <p>Families have practiced giving by caring for elders, feeding neighbors, helping new arrivals, supporting places of worship, and raising children who understand responsibility to others. Civic clubs, faith communities, mutual aid groups, immigrant associations, neighborhood nonprofits, alumni groups, and local volunteers have all carried forms of philanthropy that do not always look like formal charity from the outside.</p>
      <p>That older understanding is important because it keeps generosity human. A person does not need to wait until they are wealthy to become useful to a cause. A community does not need perfect infrastructure before it deserves support. A nonprofit does not need a polished marketing team before its work matters.</p>

      <h2>How Different Generations Give</h2>
      <p>Different generations often find their way into giving through different doors. Older donors may have built long relationships with local institutions, churches, schools, hospitals, cultural groups, and civic organizations. Their giving may be steady, private, and rooted in memory.</p>
      <p>Younger donors may discover causes through search, social conversations, workplace communities, mutual aid, direct service, crowdfunding, or urgent moments in the news. They may want to see impact, identity, values, and a path to participate beyond a payment. Many people in the middle are balancing family, work, debt, caregiving, and limited time, but still want to help in ways that fit real life.</p>
      <p>None of these styles is more morally serious than the others. They are different languages for the same instinct: something needs care, and I can contribute something.</p>

      <h2>The Problem Today</h2>
      <p>The desire to help is often stronger than the path. A donor may not know which nonprofit serves a community. A volunteer may not know who needs help. A skilled professional may not know where their knowledge would be useful. A managed fund or public institution may need clearer public context before directing support responsibly.</p>
      <p>For smaller nonprofits, the problem is often visibility, not worth. Public records may exist, but they can be fragmented. Donation and volunteer paths may be unclear. Search engines and AI tools may not understand the organization well enough to surface it when someone is ready to help. The result is a quiet loss: people who want to give and organizations that need support may never find each other.</p>

      <h2>How Daanaa Makes Philanthropy Easier</h2>
      <p>Daanaa is built around a simple belief: giving should be easier to begin and easier to continue. The platform connects public nonprofit data to stable profiles, gives donors and civic partners clearer context, and gives nonprofits a path to claim and improve their pages as the beta expands.</p>
      <p>Daanaa also treats giving as more than a transaction. A person may give money, time, knowledge, attention, or operational support. The Giving Wallet can help donors remember organizations they care about and return later without turning generosity into a public performance. The Impact Network can help donors, volunteers, skilled supporters, managed funds, and responsible partners understand where different forms of help may fit.</p>
      <p>The stewardship boundary matters. Daanaa does not process donations, hold donor funds, or make giving activity public. Nonprofits cannot pay for better profile treatment, trust language, peer context, or discovery priority. Public data, claim status, donation paths, volunteer paths, and partner offers should remain separate so people can understand the page without pressure.</p>

      <h2>Every Contributor Can Be A Philanthropist</h2>
      <p>If philanthropy only belongs to people with large resources, most people are left outside the story. That is too small a definition for the work communities actually need. A student who gives time can be a philanthropist. A retiree who shares knowledge can be a philanthropist. A small business that lowers a cost for a nonprofit can be a philanthropist. A donor who gives modestly but consistently can be a philanthropist. A neighbor who helps someone find the right organization can be a philanthropist.</p>
      <p>Daanaa's role is not to make generosity performative or to decide which contribution is most important. Its role is to make the paths easier to see, easier to trust, easier to remember, and easier to repeat. When that happens, philanthropy becomes less like a status and more like a practice.</p>
      <p>That is the world Daanaa is trying to support: one where giving is not reserved for a few, and where every sincere contributor can find a clearer way to help.</p>

      <h2>Sources</h2>
      <ul>
        <li><a href="{BASE_URL}/open-data.html">Daanaa Visibility Overlay</a></li>
        <li><a href="{BASE_URL}/blog/giving-wallet-making-giving-easier-to-repeat.html">Giving Wallet: Making giving easier to repeat</a></li>
        <li><a href="{BASE_URL}/blog/daanaa-impact-network-giving-money-time-knowledge-support.html">The Daanaa Impact Network</a></li>
        <li><a href="https://www.irs.gov/publications/p526">IRS Publication 526: Charitable Contributions</a></li>
      </ul>
    </article>
  </main>
</body>
</html>
"""
    (blog_dir / "philanthropy-belongs-to-everyone.html").write_text(philanthropy_everyone, encoding="utf-8")

def append_overlay_page_sitemap() -> None:
    today = date.today().isoformat()
    page_path = PUBLIC / "overlay-pages.xml"
    pages = [
        f"{BASE_URL}/about-daanaa.html",
        f"{BASE_URL}/answers/daanaa-faq.html",
        f"{BASE_URL}/authority/identity-kit.html",
        f"{BASE_URL}/authority/search-everywhere.html",
        f"{BASE_URL}/intent/index.html",
        f"{BASE_URL}/find/index.html",
        f"{BASE_URL}/open-data.html",
        f"{BASE_URL}/claim-nonprofit-page.html",
        f"{BASE_URL}/nonprofit-vendor-discounts.html",
        f"{BASE_URL}/llms.txt",
        f"{BASE_URL}/ai.txt",
        f"{BASE_URL}/dataset.json",
        f"{BASE_URL}/blog/why-small-nonprofits-disappear-in-search.html",
        f"{BASE_URL}/blog/how-donors-can-use-public-nonprofit-data-responsibly.html",
        f"{BASE_URL}/blog/giving-wallet-making-giving-easier-to-repeat.html",
        f"{BASE_URL}/blog/daanaa-impact-network-giving-money-time-knowledge-support.html",
        f"{BASE_URL}/blog/philanthropy-belongs-to-everyone.html",
    ]
    with page_path.open("w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for loc in pages:
            f.write("  <url>\n")
            f.write(f"    <loc>{loc}</loc>\n")
            f.write(f"    <lastmod>{today}</lastmod>\n")
            f.write("  </url>\n")
        f.write("</urlset>\n")

    index_path = PUBLIC / "sitemap-index.xml"
    text = index_path.read_text(encoding="utf-8")
    entry = f"""  <sitemap>\n    <loc>{BASE_URL}/overlay-pages.xml</loc>\n    <lastmod>{today}</lastmod>\n  </sitemap>\n"""
    growth_entry = f"""  <sitemap>\n    <loc>{BASE_URL}/growth-pages.xml</loc>\n    <lastmod>{today}</lastmod>\n  </sitemap>\n"""
    additions = ""
    if f"{BASE_URL}/overlay-pages.xml" not in text:
        additions += entry
    intent_entry = f"""  <sitemap>\n    <loc>{BASE_URL}/intent-pages.xml</loc>\n    <lastmod>{today}</lastmod>\n  </sitemap>\n"""
    if f"{BASE_URL}/growth-pages.xml" not in text and (PUBLIC / "growth-pages.xml").exists():
        additions += growth_entry
    if f"{BASE_URL}/intent-pages.xml" not in text and (PUBLIC / "intent-pages.xml").exists():
        additions += intent_entry
    if additions:
        text = text.replace("</sitemapindex>\n", additions + "</sitemapindex>\n")
        index_path.write_text(text, encoding="utf-8")


def write_growth_landing_pages() -> None:
    claim_page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Claim Your Nonprofit Page | Daanaa</title>
  <meta name="description" content="Daanaa helps nonprofits claim public profile pages, update donation and volunteer information, and help donors find clear public context.">
  <link rel="canonical" href="{BASE_URL}/claim-nonprofit-page.html">
</head>
<body>
  <main>
    <h1>Claim Your Nonprofit Page</h1>
    <p>Daanaa is building a public nonprofit discovery layer from IRS, NCCS, ProPublica, and local registry data. Nonprofits can claim their pages to improve public context for donors and volunteers.</p>
    <h2>What Claiming Should Unlock</h2>
    <ul>
      <li>Confirm the nonprofit identity and official website.</li>
      <li>Update mission, service area, and contact details.</li>
      <li>Add verified donation information when available.</li>
      <li>Add volunteer opportunities and contact paths.</li>
      <li>Correct public data issues without losing source transparency.</li>
    </ul>
    <h2>Current Discovery</h2>
    <p>Organization profile URLs use this pattern: <code>{PROFILE_BASE_URL}/org/{{ein}}</code>.</p>
    <p>EIN values in data files use nine digits without a dash. Human-facing displays may format the same EIN as <code>XX-XXXXXXX</code>.</p>
    <p><a href="{PROFILE_BASE_URL}/for-nonprofits">Go to Daanaa for nonprofits</a></p>
  </main>
</body>
</html>
"""
    (PUBLIC / "claim-nonprofit-page.html").write_text(claim_page, encoding="utf-8")

    vendor_page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nonprofit Vendor Discounts | Daanaa</title>
  <meta name="description" content="Daanaa is preparing a nonprofit-friendly vendor pathway for small businesses that serve nonprofits with transparent discounts and service offers.">
  <link rel="canonical" href="{BASE_URL}/nonprofit-vendor-discounts.html">
</head>
<body>
  <main>
    <h1>Nonprofit-Friendly Vendor Discounts</h1>
    <p>Daanaa plans to help small businesses reach nonprofits with useful services, transparent discount codes, and local support offers.</p>
    <h2>Vendor Categories</h2>
    <ul>
      <li>Bookkeeping, payroll, tax, and accounting.</li>
      <li>Grant writing, fundraising, and donor communications.</li>
      <li>Web design, printing, marketing, and local media.</li>
      <li>Insurance, HR, compliance, IT, and security.</li>
      <li>Event venues, catering, and volunteer support services.</li>
    </ul>
    <h2>Trust Rules</h2>
    <p>Vendor offers should be reviewed before public promotion. Discount terms should be clear about eligibility, expiration, geography, and limits.</p>
    <p><a href="{PROFILE_BASE_URL}/for-vendors">Go to Daanaa for vendors</a></p>
  </main>
</body>
</html>
"""
    (PUBLIC / "nonprofit-vendor-discounts.html").write_text(vendor_page, encoding="utf-8")


def write_dataset_json() -> None:
    manifest_path = PUBLIC / "visibility-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    record_count = manifest["export_record_count"]
    payload = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Daanaa Open Nonprofit Organization Index",
        "description": "A nonprofit organization discovery index generated from local Daanaa registry data and public IRS/NCCS/ProPublica-derived sources. Daanaa is the nonprofit discovery directory at https://daanaa.org, distinct from daanaa.com, Dana-branded companies, Henry Seidu Daanaa, and unrelated DANA/DANAA acronyms.",
        "keywords": ["Daanaa", "Daanaa nonprofit discovery directory", "Daanaa public nonprofit profiles", "Daanaa nonprofit data", "Daanaa hidden gems"],
        "url": f"{BASE_URL}/open-data.html",
        "creator": {"@type": "Organization", "name": "Daanaa", "url": PROFILE_BASE_URL},
        "publisher": {"@type": "Organization", "name": "Daanaa", "url": PROFILE_BASE_URL},
        "license": f"{PROFILE_BASE_URL}/legal",
        "dateModified": date.today().isoformat(),
        "includedInDataCatalog": {
            "@type": "DataCatalog",
            "name": "Daanaa Visibility Overlay",
            "url": BASE_URL,
        },
        "distribution": [
            {
                "@type": "DataDownload",
                "name": "Organizations CSV",
                "encodingFormat": "text/csv",
                "contentUrl": f"{BASE_URL}/data/orgs.csv",
            },
            {
                "@type": "DataDownload",
                "name": "Sitemap index",
                "encodingFormat": "application/xml",
                "contentUrl": f"{BASE_URL}/sitemap-index.xml",
            },
        ],
        "variableMeasured": [
            "ein",
            "name",
            "city",
            "state",
            "category_letter",
            "category_name",
            "profile_url",
        ],
        "size": str(record_count),
    }
    (PUBLIC / "dataset.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    run(
        [
            sys.executable,
            "scripts/generate_visibility_exports.py",
            "--db",
            "data/merit_registry.db",
            "--orgs-csv",
            "visibility/public/data/orgs.csv",
            "--dist",
            "visibility/public",
        ]
    )
    rewrite_sitemap_index()
    write_overlay_llms()
    write_ai_txt()
    write_overlay_open_data()
    write_about_daanaa()
    run([sys.executable, "visibility/scripts/build_answer_pages.py"])
    run([sys.executable, "visibility/scripts/build_authority_pages.py"])
    run([sys.executable, "visibility/scripts/build_intent_pages.py"])
    write_growth_landing_pages()
    write_blog_pages()
    run([sys.executable, "visibility/scripts/build_growth_pages.py"])
    append_overlay_page_sitemap()
    write_robots()
    write_dataset_json()
    inject_plausible_tracking()
    run([sys.executable, "visibility/scripts/validate_overlay.py"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
