# Enrichment Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the founder's top complaint (generic, template-like mission statements) by grounding mission and cause-tag generation in the org's real website content, and close the loop so all enrichment (mission, cause tags, website, donate_url) actually reaches `registry_enriched` — where the previous 10-task build left everything stuck in a staging table nothing read from.

**Architecture:** Per org: validate a candidate website (LLM-guessed domain + identity-match confirmation, not broad crawling) → if confirmed, fetch and cache its content → generate mission grounded in real page text (falls back to the existing NTEE-based approach if no site found) → generate cause tags informed by the (possibly-grounded) mission → generate donate_url candidate, gated through the existing proven `score_confidence()`/`identity_match()` logic → promote everything that clears its threshold directly into `registry_enriched`, inline, per-org.

**Tech Stack:** Python 3.10+, SQLite3, `requests` (already a dependency), local Qwen-32B via existing `QwenInference`/`get_real_qwen_fn()`, pytest with `pythonpath = .` (bare `pytest` works from repo root).

## Global Constraints

- Code footprint: minimal — reuse existing modules (`page_cache` schema, `score_confidence()`, `identity_match()`, `SemanticLookup`, `QwenInference`) rather than rebuilding.
- Never overwrite good existing data with a lower-confidence new guess — every promotion is additive/corrective, never destructive.
- Below-threshold donate_url results get `donate_human_review=1` (existing pattern in `donation_link_pipeline.py`), never silently written as fact.
- One bad org must never crash the batch — every per-org operation stays inside the existing `try/except Exception: logger.error(...); continue` guard in `_enrich_layer()`.
- Website validation is a single fetch + identity-match check, NOT a crawl/search loop (that approach was paused 2026-06-22 for being network-bound; this design deliberately avoids repeating it — see DECISIONS.md 2026-07-07).
- All new tests use `test_db`/`mock_qwen`/`mock_embeddings`/`enrich_config` fixtures from `tests/fixtures.py`, never the real `data/merit_registry.db`, and never a real network call.
- UA string and TIMEOUT for any HTTP fetch: reuse `donation_link_pipeline.py`'s existing `UA` (`"Mozilla/5.0 (compatible; DaanaaLinkVerifier/1.0; ...)"`) and `TIMEOUT = 10` constants rather than defining new ones.

---

## File Structure

```
scripts/
├── donate_confidence.py         (NEW — extracted score_confidence()/identity_match())
├── website_content.py           (NEW — validate candidate URL, fetch+cache content,
│                                  detect volunteer-page link)
├── donation_link_pipeline.py    (MODIFIED — imports from donate_confidence.py)
├── qwen_inference.py            (MODIFIED — new generate_mission_from_website(),
│                                  generate_tags() gains optional grounding_context)
├── enrich_batch.py              (MODIFIED — wires website validation/content-fetch/
│                                  grounded mission/donate_url into _enrich_layer(),
│                                  adds inline _promote_to_registry())
├── db_enrich_migration.py       (MODIFIED — adds volunteer_url column)
├── monitor_batch.py             (MODIFIED — per-field-type throughput/ETA)
└── gpu_night.sh                 (MODIFIED — pauses enrich_cause_tags_llm.py block)

tests/
├── test_donate_confidence.py    (NEW)
├── test_website_content.py      (NEW)
├── test_qwen_inference.py       (MODIFIED — new tests appended)
├── test_enrich_batch_integration.py  (MODIFIED — new tests appended)
└── test_monitor_batch.py        (MODIFIED — new tests appended)
```

---

## Critical Path

```
Task 1 (extract donate_confidence.py)
    ↓
Task 2 (website_content.py: validate + fetch + cache)
    ↓
Task 3 (QwenInference: grounded mission generation)
    ↓
Task 4 (QwenInference: extend generate_tags with grounding_context)
    ↓
Task 5 (DB migration: volunteer_url column)
    ↓
Task 6 (EnrichmentBatch: wire it all together + inline promotion)
    ↓
Task 7 (Integration tests: full sequenced flow, end to end)
    ↓
Task 8 (monitor_batch.py: per-field-type breakdown)
    ↓
Task 9 (gpu_night.sh + cron: pause old script, exclusive-access scheduling)
```

Tasks 1-2 have no dependency on each other and could run in either order, but Task 1
must land before Task 2 imports from it. Tasks 8-9 are independent of 1-7's logic and
could be done in parallel, but are sequenced last here for simplicity of review.

---

## Tasks

### Task 1: Extract `score_confidence()`/`identity_match()` into a shared module

**Files:**
- Create: `scripts/donate_confidence.py`
- Modify: `scripts/donation_link_pipeline.py` (replace local definitions with import)
- Test: `tests/test_donate_confidence.py`

**Interfaces:**
- Produces: `score_confidence(factors: dict) -> int`, `identity_match(org_name: str, page_text: str) -> tuple[str, float]` — both importable via `from scripts.donate_confidence import score_confidence, identity_match`

- [ ] **Step 1: Write failing tests for the extracted functions**

```python
# tests/test_donate_confidence.py
"""Tests for the extracted donate_confidence module (Task 1).

These are the exact same test cases that would validate
donation_link_pipeline.py's original score_confidence()/identity_match() —
extraction must not change behavior, only location.
"""
from scripts.donate_confidence import score_confidence, identity_match


def test_score_confidence_all_positive_factors():
    factors = {
        'found_on_official_website': True,
        'nonprofit_name_visible': True,
        'website_confidence_90': True,
        'processor_recognized': True,
        'no_suspicious_redirects': True,
        'city_state_match': True,
        'branding_matches': True,
        'link_works': True,
        'ein_visible': True,
    }
    # 30+20+15+10+10+5+5+5+5 = 105, clamped to 100
    assert score_confidence(factors) == 100


def test_score_confidence_empty_factors_is_zero():
    assert score_confidence({}) == 0


def test_score_confidence_deductions_clamp_at_zero():
    factors = {
        'name_mismatch': True,
        'website_not_official': True,
        'not_from_official_site': True,
    }
    # -40 + -30 + -25 = -95, clamped to 0
    assert score_confidence(factors) == 0


def test_score_confidence_known_partial_case():
    factors = {
        'found_on_official_website': True,  # +30
        'processor_recognized': True,        # +10
        'link_broken': True,                 # -10
    }
    assert score_confidence(factors) == 30


def test_identity_match_exact():
    level, ratio = identity_match(
        "Tech For Good Foundation",
        "Welcome to Tech For Good Foundation, providing technology training."
    )
    assert level == 'exact'
    assert ratio == 1.0


def test_identity_match_mismatch():
    level, ratio = identity_match(
        "Tech For Good Foundation",
        "This page is about completely unrelated topics with no overlap words."
    )
    assert level == 'mismatch'
    assert ratio == 0.0


def test_identity_match_stop_words_ignored():
    # "the", "of", "and", "foundation" are stop words — only "tech", "good" count
    level, ratio = identity_match(
        "The Tech and Good Foundation",
        "tech good"
    )
    assert level == 'exact'
    assert ratio == 1.0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd ~/meritgiving && source venv/bin/activate && pytest tests/test_donate_confidence.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.donate_confidence'`

- [ ] **Step 3: Create `scripts/donate_confidence.py` with the extracted functions**

Copy the exact logic from `scripts/donation_link_pipeline.py` (lines ~121-205 as of commit `b27cb676c14`):

```python
#!/usr/bin/env python3
"""
Shared donate-link confidence scoring and identity matching.

Extracted from donation_link_pipeline.py (Task 1 of the enrichment
consolidation) so the new enrichment pipeline can reuse this proven,
already-tuned logic without duplicating it. No behavior change from
the original — same factors, same weights, same identity-match algorithm.
"""
import re

# ── Identity match (no LLM) ───────────────────────────────────────────────────

_STOP_WORDS = {
    'inc', 'the', 'of', 'a', 'an', 'and', 'or', 'for', 'to', 'in', 'at', 'by',
    'corporation', 'corp', 'llc', 'ltd', 'foundation', 'association',
    'society', 'organization', 'group', 'team', 'center', 'centre',
    'church', 'ministries', 'ministry', 'services', 'service', 'fund',
}


def identity_match(org_name: str, page_text: str) -> tuple[str, float]:
    """Return (level, ratio). Levels: exact/strong/possible/weak/mismatch/unknown."""
    words     = re.findall(r'\b[a-z]+\b', org_name.lower())
    key_words = [w for w in words if w not in _STOP_WORDS and len(w) > 2][:5]
    if not key_words:
        return 'unknown', 0.0
    page_lower = page_text.lower()[:2000]
    matches    = sum(1 for w in key_words if w in page_lower)
    ratio      = matches / len(key_words)
    if ratio >= 0.8:
        return 'exact', ratio
    elif ratio >= 0.6:
        return 'strong', ratio
    elif ratio >= 0.4:
        return 'possible', ratio
    elif ratio > 0:
        return 'weak', ratio
    else:
        return 'mismatch', ratio


# ── Confidence scorer ──────────────────────────────────────────────────────────

def score_confidence(factors: dict) -> int:
    score = 0
    if factors.get('found_on_official_website'): score += 30
    if factors.get('nonprofit_name_visible'):    score += 20
    if factors.get('website_confidence_90'):     score += 15
    if factors.get('processor_recognized'):      score += 10
    if factors.get('no_suspicious_redirects'):   score += 10
    if factors.get('city_state_match'):          score +=  5
    if factors.get('branding_matches'):          score +=  5
    if factors.get('link_works'):                score +=  5
    if factors.get('ein_visible'):               score +=  5
    # Deductions
    if factors.get('generic_platform_url'):      score -= 40
    if factors.get('name_mismatch'):             score -= 40
    if factors.get('website_not_official'):      score -= 30
    if factors.get('not_from_official_site'):    score -= 25
    if factors.get('city_state_mismatch'):       score -= 20
    if factors.get('suspicious_redirect'):       score -= 20
    if factors.get('url_shortener'):             score -= 15
    if factors.get('no_visible_name'):           score -= 15
    if factors.get('processor_unknown'):         score -= 10
    if factors.get('link_broken'):               score -= 10
    if factors.get('abandoned_website'):         score -= 10
    return max(0, min(100, score))
```

- [ ] **Step 4: Update `donation_link_pipeline.py` to import instead of define locally**

In `scripts/donation_link_pipeline.py`, find the `_STOP_WORDS`, `identity_match()`, and
`score_confidence()` definitions (around lines 121-205) and replace them with an import.
Add near the top of the file, alongside the other local imports (after the line
`from check_link_health import (...)` at line 51):

```python
from scripts.donate_confidence import identity_match, score_confidence
```

Then delete the now-duplicate `_STOP_WORDS`, `identity_match()`, and `score_confidence()`
function bodies from `donation_link_pipeline.py` — the import replaces them entirely.
Leave the `# ── Identity match (no LLM) ──` and `# ── Confidence scorer (spec §15) ──`
section comments in place but pointing at the import if useful for readability, or
remove them since the logic now lives in `donate_confidence.py`'s own commented sections.

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_donate_confidence.py -v
```

Expected: 6 passed

- [ ] **Step 6: Verify `donation_link_pipeline.py` still works after the extraction**

```bash
python3 -c "from scripts.donation_link_pipeline import score_confidence, identity_match; print(score_confidence({'found_on_official_website': True})); print(identity_match('Test Org', 'test org'))"
```

Expected: prints `30` then `('exact', 1.0)` — confirms the re-exported names still work
for any other code that imports them from `donation_link_pipeline` directly.

- [ ] **Step 7: Commit**

```bash
git add scripts/donate_confidence.py scripts/donation_link_pipeline.py tests/test_donate_confidence.py
git commit -m "refactor: extract score_confidence/identity_match into shared donate_confidence module

Mechanical extraction, no behavior change — lets the new enrichment
pipeline reuse this proven confidence-scoring logic instead of
rebuilding it. donation_link_pipeline.py now imports from the shared
module rather than defining these functions locally."
```

---

### Task 2: Website content validation and fetch module

**Files:**
- Create: `scripts/website_content.py`
- Test: `tests/test_website_content.py`

**Interfaces:**
- Consumes: `identity_match()` from Task 1 (`scripts.donate_confidence`)
- Produces: `validate_and_fetch_website(db_con: sqlite3.Connection, ein: str, org_name: str, candidate_url: str) -> dict | None` — returns `None` if the candidate URL doesn't resolve or fails identity match; otherwise returns `{'url': str, 'content_text': str, 'identity_level': str, 'identity_ratio': float, 'volunteer_url': str | None}`. Also produces `extract_text_content(html: str) -> str` and `find_volunteer_link(html: str, base_url: str) -> str | None` as separately-testable helpers.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_website_content.py
"""Tests for website_content.py (Task 2).

validate_and_fetch_website() makes a real HTTP request, so its own
integration behavior is tested via mocking requests.get/head — no real
network calls in this test file. extract_text_content() and
find_volunteer_link() are pure functions tested directly against
sample HTML.
"""
from unittest.mock import patch, MagicMock
from scripts.website_content import (
    validate_and_fetch_website,
    extract_text_content,
    find_volunteer_link,
)


SAMPLE_HTML = """
<html><head><title>Tech For Good Foundation</title></head>
<body>
<nav><a href="/about">About</a><a href="/volunteer">Volunteer With Us</a><a href="/donate">Donate</a></nav>
<main>
<h1>Tech For Good Foundation</h1>
<p>We provide free coding bootcamps and laptop donations to underserved youth
in San Francisco. Since 2015, we've trained over 400 students through our
after-school Saturday Robotics Academy program.</p>
</main>
</body></html>
"""

NO_VOLUNTEER_HTML = """
<html><body><nav><a href="/about">About</a><a href="/donate">Donate</a></nav>
<p>Some org content here.</p></body></html>
"""


def test_extract_text_content_strips_html_tags():
    text = extract_text_content(SAMPLE_HTML)
    assert "coding bootcamps" in text
    assert "Saturday Robotics Academy" in text
    assert "<p>" not in text
    assert "<nav>" not in text


def test_extract_text_content_empty_html_returns_empty_string():
    assert extract_text_content("") == ""
    assert extract_text_content("<html></html>") == ""


def test_find_volunteer_link_detects_volunteer_page():
    link = find_volunteer_link(SAMPLE_HTML, base_url="https://techforgood.org")
    assert link == "https://techforgood.org/volunteer"


def test_find_volunteer_link_returns_none_when_absent():
    link = find_volunteer_link(NO_VOLUNTEER_HTML, base_url="https://someorg.org")
    assert link is None


def test_find_volunteer_link_handles_get_involved_phrasing():
    html = '<a href="/get-involved">Get Involved</a>'
    link = find_volunteer_link(html, base_url="https://someorg.org")
    assert link == "https://someorg.org/get-involved"


@patch('scripts.website_content.requests.get')
def test_validate_and_fetch_website_success(mock_get, test_db):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = SAMPLE_HTML
    mock_resp.content = SAMPLE_HTML.encode()
    mock_get.return_value = mock_resp

    result = validate_and_fetch_website(
        db_con=test_db,
        ein='611234567',
        org_name='Tech For Good Foundation',
        candidate_url='techforgood.org'
    )

    assert result is not None
    assert result['identity_level'] in ('exact', 'strong')
    assert "coding bootcamps" in result['content_text']
    assert result['volunteer_url'] == 'https://techforgood.org/volunteer'


@patch('scripts.website_content.requests.get')
def test_validate_and_fetch_website_identity_mismatch_returns_none(mock_get, test_db):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "<html><body>Completely unrelated content about something else.</body></html>"
    mock_resp.content = mock_resp.text.encode()
    mock_get.return_value = mock_resp

    result = validate_and_fetch_website(
        db_con=test_db,
        ein='611234567',
        org_name='Tech For Good Foundation',
        candidate_url='wrongsite.org'
    )

    assert result is None


@patch('scripts.website_content.requests.get')
def test_validate_and_fetch_website_connection_error_returns_none(mock_get, test_db):
    import requests
    mock_get.side_effect = requests.exceptions.ConnectionError("refused")

    result = validate_and_fetch_website(
        db_con=test_db,
        ein='611234567',
        org_name='Tech For Good Foundation',
        candidate_url='doesnotexist.org'
    )

    assert result is None


@patch('scripts.website_content.requests.get')
def test_validate_and_fetch_website_caches_page(mock_get, test_db):
    """Confirms the fetched page gets cached via page_cache (reused schema)."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = SAMPLE_HTML
    mock_resp.content = SAMPLE_HTML.encode()
    mock_get.return_value = mock_resp

    cursor = test_db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS page_cache (
            url TEXT PRIMARY KEY, ein TEXT, fetched_at TEXT,
            status_code INTEGER, html_gz BLOB, content_len INTEGER
        )
    """)
    test_db.commit()

    validate_and_fetch_website(
        db_con=test_db, ein='611234567',
        org_name='Tech For Good Foundation', candidate_url='techforgood.org'
    )

    cursor.execute("SELECT COUNT(*) FROM page_cache WHERE ein = ?", ('611234567',))
    assert cursor.fetchone()[0] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_website_content.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.website_content'`

- [ ] **Step 3: Implement `scripts/website_content.py`**

```python
#!/usr/bin/env python3
"""
Website content validation and fetch for the enrichment pipeline.

Given a CANDIDATE domain (produced by QwenInference.generate_website()'s
LLM guess informed by similar-org context), validates it's really that
org's site via a single fetch + identity_match() check — not a search or
crawl. If confirmed, extracts clean text content for mission-grounding
and looks for a volunteer/get-involved page link.

This is deliberately a single targeted fetch, not the broader crawling
approach (web_finder_agent.py) paused 2026-06-22 for being network-bound —
see DECISIONS.md 2026-07-07 for why this is a different, lighter mechanism.
"""
import re
import zlib
import sqlite3
import datetime
from typing import Optional, Dict
from urllib.parse import urljoin, urlparse

import requests

from scripts.donate_confidence import identity_match

UA = ("Mozilla/5.0 (compatible; DaanaaLinkVerifier/1.0; "
      "+https://daanaa.org/about)")
TIMEOUT = 10

_VOLUNTEER_PATTERNS = re.compile(
    r'volunteer|get[\s-]?involved', re.IGNORECASE
)

_TAG_RE = re.compile(r'<[^>]+>')
_SCRIPT_STYLE_RE = re.compile(
    r'<(script|style|nav|header|footer)[^>]*>.*?</\1>',
    re.IGNORECASE | re.DOTALL
)
_WHITESPACE_RE = re.compile(r'\s+')


def extract_text_content(html: str) -> str:
    """Strip HTML tags, scripts, styles, and nav/header/footer chrome,
    returning cleaned body text suitable for LLM grounding context."""
    if not html:
        return ""
    stripped = _SCRIPT_STYLE_RE.sub(' ', html)
    stripped = _TAG_RE.sub(' ', stripped)
    stripped = _WHITESPACE_RE.sub(' ', stripped).strip()
    return stripped


def find_volunteer_link(html: str, base_url: str) -> Optional[str]:
    """Scan anchor tags for a volunteer/get-involved page link.
    Returns the absolute URL, or None if no such link is found."""
    if not html:
        return None
    for match in re.finditer(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>', html, re.IGNORECASE):
        href, link_text = match.group(1), match.group(2)
        if _VOLUNTEER_PATTERNS.search(href) or _VOLUNTEER_PATTERNS.search(link_text):
            return urljoin(base_url, href)
    return None


def _cache_page(db_con: sqlite3.Connection, ein: str, url: str, body: bytes, status_code: int):
    """Store compressed HTML in the shared page_cache table (same schema
    donation_link_pipeline.py uses) so future pipeline runs can reuse it."""
    compressed = zlib.compress(body, level=6)
    fetched_at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    db_con.execute("""
        INSERT OR REPLACE INTO page_cache (url, ein, fetched_at, status_code, html_gz, content_len)
        VALUES (?,?,?,?,?,?)
    """, (url, ein, fetched_at, status_code, compressed, len(body)))
    db_con.commit()


def validate_and_fetch_website(
    db_con: sqlite3.Connection,
    ein: str,
    org_name: str,
    candidate_url: str
) -> Optional[Dict]:
    """
    Fetch a candidate URL once, confirm it's really the named org's site via
    identity_match(), and if confirmed, extract content + look for a
    volunteer page. Returns None on any failure (network error, non-200,
    identity mismatch) — the caller falls back to non-grounded generation.

    Returns dict: {'url': str, 'content_text': str, 'identity_level': str,
                   'identity_ratio': float, 'volunteer_url': str|None}
    """
    url = candidate_url
    if not url.startswith('http'):
        url = f'https://{url}'

    try:
        resp = requests.get(
            url, timeout=TIMEOUT, allow_redirects=True,
            headers={"User-Agent": UA, "Accept": "text/html,*/*"}
        )
    except requests.exceptions.RequestException:
        return None

    if resp.status_code != 200:
        return None

    html = resp.text
    level, ratio = identity_match(org_name, html)
    if level in ('mismatch', 'unknown', 'weak'):
        return None

    _cache_page(db_con, ein, url, resp.content, resp.status_code)

    content_text = extract_text_content(html)
    volunteer_url = find_volunteer_link(html, base_url=url)

    return {
        'url': url,
        'content_text': content_text[:2000],  # cap for prompt-size sanity
        'identity_level': level,
        'identity_ratio': ratio,
        'volunteer_url': volunteer_url,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_website_content.py -v
```

Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/website_content.py tests/test_website_content.py
git commit -m "feat: website content validation and fetch module

validate_and_fetch_website() confirms a candidate domain is really the
named org's site via a single fetch + identity_match() check (not a
crawl/search), caches the page via the shared page_cache schema, and
extracts clean text content + a volunteer-page link if present. This
is the input the next task uses to ground mission generation in real
website text instead of guessing from NTEE code alone."
```

---

### Task 3: Website-grounded mission generation

**Files:**
- Modify: `scripts/qwen_inference.py`
- Modify: `scripts/enrich_batch_config.json` (add mission prompt template)
- Test: `tests/test_qwen_inference.py` (append new tests)

**Interfaces:**
- Consumes: nothing new from earlier tasks directly (this is a QwenInference method, called later by Task 6 with output from Task 2)
- Produces: `QwenInference.generate_mission_from_website(org_data: Dict[str, Any], website_content: str, max_retries: int = 1) -> Optional[str]`

- [ ] **Step 1: Write failing tests**

```python
# Append to tests/test_qwen_inference.py

def test_generate_mission_from_website_returns_string(mock_qwen, enrich_config):
    """Basic contract: given org data + website content, returns a mission string."""
    qwen = QwenInference(qwen_fn=mock_qwen, config=enrich_config, prompt_version='v1.0')

    org_data = {'EIN': '123', 'name': 'Tech Academy', 'ntee': 'B25'}
    website_content = (
        "We provide free coding bootcamps and laptop donations to underserved "
        "youth in San Francisco. Since 2015, we've trained over 400 students "
        "through our after-school Saturday Robotics Academy program."
    )

    result = qwen.generate_mission_from_website(org_data, website_content)

    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_mission_from_website_prompt_includes_real_content(enrich_config):
    """The prompt sent to Qwen must include the actual website text, not
    just NTEE/location — this is the whole point of grounding. Uses an echo
    mock (not mock_qwen) to inspect exactly what was sent."""
    captured_prompts = []

    def echo_qwen(prompt: str, max_tokens: int = 200) -> str:
        captured_prompts.append(prompt)
        return "A specific, grounded mission sentence."

    qwen = QwenInference(qwen_fn=echo_qwen, config=enrich_config, prompt_version='v1.0')

    org_data = {'EIN': '123', 'name': 'Tech Academy', 'ntee': 'B25'}
    website_content = "Saturday Robotics Academy trains 400 students in coding."

    qwen.generate_mission_from_website(org_data, website_content)

    assert len(captured_prompts) == 1
    assert "Saturday Robotics Academy" in captured_prompts[0]
    assert "Tech Academy" in captured_prompts[0]


def test_generate_mission_from_website_timeout_returns_none(enrich_config):
    """Deterministic timeout mock — same pattern as the existing
    test_qwen_timeout_returns_none test for generate_tags/generate_website."""
    def timeout_qwen(prompt: str, max_tokens: int = 200) -> str:
        raise TimeoutError("Qwen timeout")

    qwen = QwenInference(qwen_fn=timeout_qwen, config=enrich_config, prompt_version='v1.0')
    org_data = {'EIN': '123', 'name': 'Org', 'ntee': 'B25'}

    result = qwen.generate_mission_from_website(org_data, "some website content", max_retries=1)

    assert result is None


def test_generate_mission_from_website_empty_content_still_works(mock_qwen, enrich_config):
    """Empty website_content (e.g., a page that fetched but had no useful
    text) should not crash — falls through to a generic-but-valid prompt."""
    qwen = QwenInference(qwen_fn=mock_qwen, config=enrich_config, prompt_version='v1.0')
    org_data = {'EIN': '123', 'name': 'Org', 'ntee': 'B25'}

    result = qwen.generate_mission_from_website(org_data, "")

    assert result is None or isinstance(result, str)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_qwen_inference.py -v -k "mission_from_website"
```

Expected: FAIL with `AttributeError: 'QwenInference' object has no attribute 'generate_mission_from_website'`

- [ ] **Step 3: Add the `mission` prompt template to `scripts/enrich_batch_config.json`**

Add a `"mission"` key alongside the existing `"cause_tags"` and `"website"` keys in
both `"v1.0"` and `"v1.1"` prompt versions:

```json
{
  "prompts": {
    "v1.0": {
      "cause_tags": "Similar high-performing orgs are tagged with: {similar_tags}. This organization has the mission: {mission}. NTEE category: {ntee}. Suggest 3-5 cause tags that best describe this organization's focus area.",
      "website": "Similar organizations in {city}, {state} use domains like: {similar_domains}. This organization is named: {org_name}. Suggest the most likely domain name (e.g., myorg.org).",
      "mission": "This organization is named: {org_name}. Here is real text from their website:\n\n{website_content}\n\nWrite a specific, one-sentence mission statement for this organization based on what their website actually says they do. Be concrete — mention specific programs, populations served, or activities if the website describes them. Do not write a generic sentence that could apply to any nonprofit in their sector."
    },
    "v1.1": {
      "cause_tags": "Similar high-performing orgs in {ntee} are tagged with: {similar_tags}. This organization has the mission: {mission}. NTEE category: {ntee}. For {ntee_label} organizations, emphasize: {ntee_emphasis}. Suggest 3-5 cause tags.",
      "website": "Similar organizations in {city}, {state} use domains like: {similar_domains}. This organization is named: {org_name}. Common patterns in {state}: {state_patterns}. Suggest the most likely domain.",
      "mission": "This organization is named: {org_name}. Here is real text from their website:\n\n{website_content}\n\nWrite a specific, one-sentence mission statement for this organization based on what their website actually says they do. Be concrete — mention specific programs, populations served, or activities if the website describes them. Do not write a generic sentence that could apply to any nonprofit in their sector."
    }
  }
}
```

Also update `tests/fixtures.py`'s implicit expectation — no change needed there, since
`enrich_config` fixture loads this JSON file directly, so the new `"mission"` key is
automatically available to tests once the JSON file is updated.

- [ ] **Step 4: Implement `generate_mission_from_website()` in `scripts/qwen_inference.py`**

Add this method to the `QwenInference` class, following the exact same pattern as
`generate_tags()`/`generate_website()` (same retry/timeout/exception handling):

```python
    def generate_mission_from_website(
        self,
        org_data: Dict[str, Any],
        website_content: str,
        max_retries: int = 1
    ) -> Optional[str]:
        """Generate a mission statement grounded in real website text.

        This is the fix for generic, template-like missions (e.g. "Provides
        educational services in City, State") — instead of guessing from
        NTEE code + city/state alone, this grounds generation in what the
        org's own website actually says, when a validated site is available.
        Callers should fall back to NTEE-based generation (not this method)
        when no validated website content exists.
        """
        prompt = self._build_mission_prompt(org_data, website_content)

        for attempt in range(max_retries):
            try:
                result = self.qwen_fn(prompt=prompt, max_tokens=150)
                if result:
                    return result.strip()
            except TimeoutError:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    print(f"[ERROR] Qwen timeout generating mission for {org_data.get('EIN', 'unknown')}")
                    return None
            except Exception as e:
                print(f"[ERROR] Qwen error generating mission for {org_data.get('EIN', 'unknown')}: {e}")
                return None

        return None

    def _build_mission_prompt(
        self,
        org_data: Dict[str, Any],
        website_content: str
    ) -> str:
        template = self.prompts.get('mission', '')
        return template.format(
            org_name=org_data.get('name', ''),
            website_content=website_content or 'No specific content available.'
        )
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_qwen_inference.py -v
```

Expected: all tests pass, including the 4 new ones

- [ ] **Step 6: Commit**

```bash
git add scripts/qwen_inference.py scripts/enrich_batch_config.json tests/test_qwen_inference.py
git commit -m "feat: website-grounded mission generation in QwenInference

Adds generate_mission_from_website() — grounds mission text in real
website content instead of guessing from NTEE code + location alone.
This is the fix for the generic 'Provides X in City, State' pattern
found in ~99% of current missions (only ~1% currently use any web
context). Follows the exact retry/timeout/error pattern already
established in generate_tags()/generate_website()."
```

---

### Task 4: Extend `generate_tags()` with optional grounding context

**Files:**
- Modify: `scripts/qwen_inference.py`
- Test: `tests/test_qwen_inference.py` (append)

**Interfaces:**
- Produces: `QwenInference.generate_tags(org_data, similar_orgs, max_retries=1, grounding_context: Optional[str] = None) -> Optional[str]` — extends the existing signature with one new optional parameter; existing callers passing only `(org_data, similar_orgs)` are unaffected.

- [ ] **Step 1: Write failing tests**

```python
# Append to tests/test_qwen_inference.py

def test_generate_tags_without_grounding_context_unchanged(mock_qwen, enrich_config):
    """Backward compatibility: existing 2-arg calls must still work exactly
    as before — this is a non-breaking extension, not a replacement."""
    qwen = QwenInference(qwen_fn=mock_qwen, config=enrich_config, prompt_version='v1.0')
    org_data = {'EIN': '123', 'name': 'Org', 'mission': 'Test mission', 'ntee': 'B25'}

    result = qwen.generate_tags(org_data, similar_orgs=[])

    assert isinstance(result, str)


def test_generate_tags_with_grounding_context_included_in_prompt(enrich_config):
    """When grounding_context is provided (real website text), it must
    appear in the prompt sent to Qwen — this is what lets cause tags be
    informed by real site content, not just the (possibly still-generic)
    mission field alone."""
    captured_prompts = []

    def echo_qwen(prompt: str, max_tokens: int = 200) -> str:
        captured_prompts.append(prompt)
        return "Education, Youth Development"

    qwen = QwenInference(qwen_fn=echo_qwen, config=enrich_config, prompt_version='v1.0')
    org_data = {'EIN': '123', 'name': 'Org', 'mission': 'Generic mission', 'ntee': 'B25'}
    grounding = "Saturday Robotics Academy trains 400 students in coding and robotics."

    qwen.generate_tags(org_data, similar_orgs=[], grounding_context=grounding)

    assert len(captured_prompts) == 1
    assert "Saturday Robotics Academy" in captured_prompts[0]


def test_generate_tags_without_grounding_context_prompt_unchanged(enrich_config):
    """When grounding_context is None (the default), the prompt must be
    byte-identical to the pre-Task-4 prompt — confirms zero behavior change
    for the common case where no website was found/validated."""
    captured_prompts = []

    def echo_qwen(prompt: str, max_tokens: int = 200) -> str:
        captured_prompts.append(prompt)
        return "Education"

    qwen = QwenInference(qwen_fn=echo_qwen, config=enrich_config, prompt_version='v1.0')
    org_data = {'EIN': '123', 'name': 'Org', 'mission': 'Test mission', 'ntee': 'B25'}

    qwen.generate_tags(org_data, similar_orgs=[])
    prompt_without_grounding = captured_prompts[0]

    captured_prompts.clear()
    qwen.generate_tags(org_data, similar_orgs=[], grounding_context=None)
    prompt_with_none = captured_prompts[0]

    assert prompt_without_grounding == prompt_with_none
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_qwen_inference.py -v -k "grounding_context"
```

Expected: FAIL — `generate_tags()` doesn't accept a `grounding_context` keyword argument yet

- [ ] **Step 3: Extend `generate_tags()` and `_build_cause_tags_prompt()`**

Modify the existing `generate_tags()` method signature and `_build_cause_tags_prompt()`
in `scripts/qwen_inference.py`:

```python
    def generate_tags(
        self,
        org_data: Dict[str, Any],
        similar_orgs: list[Dict[str, Any]],
        max_retries: int = 1,
        grounding_context: Optional[str] = None
    ) -> Optional[str]:
        prompt = self._build_cause_tags_prompt(org_data, similar_orgs, grounding_context)

        for attempt in range(max_retries):
            try:
                result = self.qwen_fn(prompt=prompt, max_tokens=150)
                if result:
                    return result.strip()
            except TimeoutError:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    print(f"[ERROR] Qwen timeout generating tags for {org_data.get('EIN', 'unknown')}")
                    return None
            except Exception as e:
                print(f"[ERROR] Qwen error for {org_data.get('EIN', 'unknown')}: {e}")
                return None

        return None
```

```python
    def _build_cause_tags_prompt(
        self,
        org_data: Dict[str, Any],
        similar_orgs: list[Dict[str, Any]],
        grounding_context: Optional[str] = None
    ) -> str:
        similar_tags = ', '.join([
            org.get('cause_tags', '').split(',')[0]
            for org in similar_orgs[:3]
            if org.get('cause_tags')
        ])

        ntee_label = org_data.get('ntee', '?')
        ntee_emphasis = self._get_ntee_emphasis(ntee_label)

        template = self.prompts.get('cause_tags', '')
        prompt = template.format(
            similar_tags=similar_tags or 'Community, Education',
            org_name=org_data.get('name', ''),
            mission=org_data.get('mission', ''),
            ntee=ntee_label,
            ntee_label=self._ntee_label(ntee_label),
            ntee_emphasis=ntee_emphasis
        )

        if grounding_context:
            prompt += f"\n\nAdditional context from the organization's website: {grounding_context}"

        return prompt
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_qwen_inference.py -v
```

Expected: all pass, including the 3 new tests and all pre-existing `generate_tags()` tests
(confirming backward compatibility)

- [ ] **Step 5: Commit**

```bash
git add scripts/qwen_inference.py tests/test_qwen_inference.py
git commit -m "feat: extend generate_tags() with optional grounding_context

Non-breaking extension — existing 2-arg calls are byte-identical in
prompt output (verified by test). When grounding_context is provided
(real website text from Task 2), it's appended to the prompt so cause
tags can be informed by actual site content, not just the mission
field (which may itself still be generic for orgs without a
validated website)."
```

---

### Task 5: Add `volunteer_url` column to schema

**Files:**
- Modify: `scripts/db_enrich_migration.py`
- Modify: `tests/fixtures.py` (`test_db` fixture's `registry_enriched` schema)
- Test: `tests/test_enrich_batch.py` (append)

**Interfaces:**
- Produces: `registry_enriched.volunteer_url TEXT` column, added idempotently (only if missing)

- [ ] **Step 1: Write failing test**

```python
# Append to tests/test_enrich_batch.py

def test_migrate_adds_volunteer_url_column():
    """volunteer_url must exist on registry_enriched after migrate() runs,
    since Task 2's website_content.py discovers this and Task 6 needs
    somewhere to write it."""
    import sqlite3
    con = sqlite3.connect(':memory:')
    cursor = con.cursor()
    cursor.execute("""
        CREATE TABLE registry_enriched (
            EIN TEXT PRIMARY KEY, organization_name TEXT
        )
    """)
    con.commit()

    from scripts.db_enrich_migration import migrate
    migrate(con)

    cols = {row[1] for row in cursor.execute("PRAGMA table_info(registry_enriched)")}
    assert 'volunteer_url' in cols
    con.close()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_enrich_batch.py::test_migrate_adds_volunteer_url_column -v
```

Expected: FAIL — `volunteer_url` not in columns

- [ ] **Step 3: Add the column-add logic to `migrate()` in `scripts/db_enrich_migration.py`**

Add this block inside `migrate()`, after the existing table-creation statements and
before the `con.commit()` call:

```python
    # Add volunteer_url to registry_enriched if missing (idempotent — same
    # pattern donation_link_pipeline.py uses for its own new columns).
    existing_cols = {r[1] for r in cursor.execute("PRAGMA table_info(registry_enriched)")}
    if 'volunteer_url' not in existing_cols:
        cursor.execute("ALTER TABLE registry_enriched ADD COLUMN volunteer_url TEXT")
```

- [ ] **Step 4: Add `volunteer_url` to the `test_db` fixture's schema in `tests/fixtures.py`**

In the `test_db` fixture, add `volunteer_url TEXT` to the `registry_enriched` CREATE
TABLE statement (after the `street_address TEXT, cohort_context TEXT` line):

```python
            street_address TEXT, cohort_context TEXT,
            volunteer_url TEXT
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_enrich_batch.py tests/test_fixtures.py -v
```

Expected: all pass, including the new migration test

- [ ] **Step 6: Commit**

```bash
git add scripts/db_enrich_migration.py tests/fixtures.py tests/test_enrich_batch.py
git commit -m "feat: add volunteer_url column to registry_enriched

Idempotent ALTER TABLE, same pattern as donation_link_pipeline.py's
existing column additions. Stores the volunteer/get-involved page URL
found by Task 2's website_content.py during the same fetch used for
mission grounding — near-zero marginal cost since the page is already
being fetched. Not yet consumed by any UI; stored for future use."
```

---

### Task 6: Wire it all together in `EnrichmentBatch` + inline promotion

**Files:**
- Modify: `scripts/enrich_batch.py`
- Test: `tests/test_enrich_batch_integration.py` (append)

**Interfaces:**
- Consumes: `validate_and_fetch_website()` from Task 2, `generate_mission_from_website()` and extended `generate_tags()` from Tasks 3-4, `identity_match()`/`score_confidence()` from Task 1, `volunteer_url` column from Task 5
- Produces: `EnrichmentBatch._enrich_layer()` (modified), `EnrichmentBatch._promote_to_registry()` (new method)

- [ ] **Step 1: Write failing integration tests**

```python
# Append to tests/test_enrich_batch_integration.py

from unittest.mock import patch, MagicMock


class TestConsolidatedEnrichment:
    """Tests for Task 6: website validation -> grounded mission -> tags ->
    inline promotion, wired into EnrichmentBatch."""

    def test_promotion_writes_to_registry_enriched_directly(self, test_db, mock_qwen, mock_embeddings, enrich_config):
        """The core fix: previously nothing promoted enrichment_run rows
        into registry_enriched, so nothing was ever visible on daanaa.org.
        This confirms promotion actually happens for fields that don't
        require website validation (cause_tags is generated regardless of
        whether a website was found)."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO registry_enriched
            (EIN, organization_name, NTEE1, mission, cause_tags, website)
            VALUES ('999888777', 'Test Nonprofit', 'B', 'Old generic mission', '', '')
        """)
        test_db.commit()

        from scripts.enrich_batch import EnrichmentBatch

        # No website candidate validates in this test (website discovery is
        # mocked to return None) — cause_tags must still promote, since tag
        # generation doesn't depend on a validated website. website must NOT
        # promote: writing an unvalidated LLM guess as the org's official
        # site would be exactly the overconfident behavior Task 2's
        # validation step exists to prevent.
        with patch('scripts.enrich_batch.validate_and_fetch_website', return_value=None):
            batch = EnrichmentBatch(
                db_con=test_db, qwen_fn=mock_qwen, embeddings_fn=mock_embeddings,
                config=enrich_config
            )
            batch.run(dry_run=False, max_orgs=1)

        cursor.execute("SELECT cause_tags, website FROM registry_enriched WHERE EIN = ?", ('999888777',))
        cause_tags, website = cursor.fetchone()
        assert cause_tags        # non-empty, was promoted
        assert website in (None, '')  # NOT promoted — unvalidated guess must not become fact

    def test_grounded_mission_used_when_website_validates(self, test_db, mock_qwen, mock_embeddings, enrich_config):
        """When Task 2's validation succeeds, mission generation should use
        generate_mission_from_website() (grounded), not the NTEE fallback."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO registry_enriched
            (EIN, organization_name, NTEE1, mission, mission_source, cause_tags, website)
            VALUES ('888777666', 'Grounded Test Org', 'B', 'Generic old mission', 'ai_ntee', '', '')
        """)
        test_db.commit()

        fake_website_result = {
            'url': 'https://groundedtestorg.org',
            'content_text': 'We run a Saturday coding academy for 200 students.',
            'identity_level': 'exact',
            'identity_ratio': 1.0,
            'volunteer_url': 'https://groundedtestorg.org/volunteer',
        }

        from scripts.enrich_batch import EnrichmentBatch

        with patch('scripts.enrich_batch.validate_and_fetch_website', return_value=fake_website_result):
            batch = EnrichmentBatch(
                db_con=test_db, qwen_fn=mock_qwen, embeddings_fn=mock_embeddings,
                config=enrich_config
            )
            batch.run(dry_run=False, max_orgs=1)

        cursor.execute(
            "SELECT mission, mission_source, volunteer_url FROM registry_enriched WHERE EIN = ?",
            ('888777666',)
        )
        mission, mission_source, volunteer_url = cursor.fetchone()
        assert mission != 'Generic old mission'  # was regenerated
        assert mission_source == 'ai_web_grounded'
        assert volunteer_url == 'https://groundedtestorg.org/volunteer'

    def test_promotion_never_overwrites_good_existing_data_with_failure(self, test_db, mock_embeddings, enrich_config):
        """If Qwen fails for an org (returns None), existing good data in
        registry_enriched must be left untouched, not nulled out."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO registry_enriched
            (EIN, organization_name, NTEE1, mission, cause_tags, website)
            VALUES ('777666555', 'Org With Existing Data', 'B', 'Existing mission', '', '')
        """)
        test_db.commit()

        def failing_qwen(prompt: str, max_tokens: int = 200) -> str:
            raise Exception("simulated failure")

        from scripts.enrich_batch import EnrichmentBatch

        with patch('scripts.enrich_batch.validate_and_fetch_website', return_value=None):
            batch = EnrichmentBatch(
                db_con=test_db, qwen_fn=failing_qwen, embeddings_fn=mock_embeddings,
                config=enrich_config
            )
            batch.run(dry_run=False, max_orgs=1)

        cursor.execute("SELECT mission, cause_tags FROM registry_enriched WHERE EIN = ?", ('777666555',))
        mission, cause_tags = cursor.fetchone()
        assert mission == 'Existing mission'  # untouched
        assert cause_tags == ''  # untouched (empty, not corrupted)

    def test_donate_url_below_threshold_flagged_for_human_review(self, test_db, mock_embeddings, enrich_config):
        """Low-confidence donate_url candidates must set donate_human_review=1
        and NOT be written as the live donate_url — existing pattern from
        donation_link_pipeline.py, must be preserved here."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO registry_enriched
            (EIN, organization_name, NTEE1, mission, cause_tags, website, donate_url, donate_human_review)
            VALUES ('666555444', 'Low Confidence Org', 'B', 'Test mission', 'Education', 'testorg.org', NULL, NULL)
        """)
        test_db.commit()

        # A donate_fn that returns a candidate with no corroborating evidence
        # at all (empty page content) -> identity_match returns 'mismatch' or
        # 'unknown' -> score_confidence stays low -> must be flagged, not written.
        def low_confidence_qwen(prompt: str, max_tokens: int = 200) -> str:
            if "donate" in prompt.lower():
                return "unrelatedcharity.org/give"
            return "Education, Community"

        from scripts.enrich_batch import EnrichmentBatch

        with patch('scripts.enrich_batch.validate_and_fetch_website', return_value=None):
            batch = EnrichmentBatch(
                db_con=test_db, qwen_fn=low_confidence_qwen, embeddings_fn=mock_embeddings,
                config=enrich_config
            )
            batch.run(dry_run=False, max_orgs=1)

        cursor.execute(
            "SELECT donate_url, donate_human_review FROM registry_enriched WHERE EIN = ?",
            ('666555444',)
        )
        donate_url, donate_human_review = cursor.fetchone()
        assert donate_url is None  # not written — below threshold
        assert donate_human_review == 1  # flagged for review
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_enrich_batch_integration.py -v -k "TestConsolidatedEnrichment"
```

Expected: FAIL — `validate_and_fetch_website` not imported/used in `enrich_batch.py` yet,
`_promote_to_registry` doesn't exist, `mission_source` values don't match

- [ ] **Step 3: Wire everything into `scripts/enrich_batch.py`**

Add the new import near the top (with the other `scripts.X` imports):

```python
from scripts.website_content import validate_and_fetch_website
from scripts.donate_confidence import score_confidence, identity_match
```

Replace the entire `_enrich_layer()` method with this sequenced version:

```python
    def _enrich_layer(
        self,
        max_orgs: Optional[int] = None,
        batch_size: int = 20
    ) -> list:
        cursor = self.db.cursor()

        query = """
            SELECT EIN, organization_name, mission, mission_source, NTEE1, city, state, donate_url
            FROM registry_enriched
            WHERE (cause_tags IS NULL OR cause_tags = '')
               OR (website IS NULL OR website = '')
               OR (mission_source IN ('ai_ntee', 'template_ntee') OR mission_source IS NULL)
            LIMIT ?
        """
        cursor.execute(query, (max_orgs or 1000000,))
        orgs = cursor.fetchall()

        results = []
        for ein, name, mission, mission_source, ntee, city, state, existing_donate_url in orgs:
            try:
                org_data = {
                    'EIN': ein, 'name': name, 'mission': mission,
                    'ntee': ntee, 'city': city, 'state': state
                }

                similar_orgs = self.semantic.find_similar_orgs(org_ein=ein, count=5)

                # Website: guess a candidate domain, then validate with a
                # single fetch + identity check (not a crawl/search loop).
                candidate_website = self.qwen.generate_website(org_data, similar_orgs)
                website_result = None
                if candidate_website:
                    website_result = validate_and_fetch_website(
                        db_con=self.db, ein=ein, org_name=name,
                        candidate_url=candidate_website
                    )

                if website_result:
                    results.append({
                        'org_ein': ein, 'enrichment_type': 'website',
                        'generated_value': website_result['url'], 'confidence_score': 0.9,
                        'context_used': json.dumps({'identity_level': website_result['identity_level']}),
                        'prompt_version': self.qwen.prompt_version
                    })
                    if website_result.get('volunteer_url'):
                        results.append({
                            'org_ein': ein, 'enrichment_type': 'volunteer_url',
                            'generated_value': website_result['volunteer_url'], 'confidence_score': 0.9,
                            'context_used': '{}', 'prompt_version': self.qwen.prompt_version
                        })

                # Mission: grounded in real website content if validated,
                # else fall back to the existing NTEE/similar-org approach —
                # but only regenerate if the current mission is weak/missing.
                grounding_context = website_result['content_text'] if website_result else None
                if mission_source in (None, 'ai_ntee', 'template_ntee') or not mission:
                    if grounding_context:
                        new_mission = self.qwen.generate_mission_from_website(org_data, grounding_context)
                        new_mission_source = 'ai_web_grounded'
                    else:
                        new_mission = None
                        new_mission_source = None
                    if new_mission:
                        results.append({
                            'org_ein': ein, 'enrichment_type': 'mission',
                            'generated_value': new_mission, 'confidence_score': 0.85,
                            'context_used': json.dumps({'mission_source': new_mission_source}),
                            'prompt_version': self.qwen.prompt_version
                        })
                        org_data['mission'] = new_mission  # feed forward to tags below

                # Cause tags: informed by (possibly-regenerated) mission +
                # website content when available.
                tags = self.qwen.generate_tags(org_data, similar_orgs, grounding_context=grounding_context)
                if tags:
                    results.append({
                        'org_ein': ein, 'enrichment_type': 'cause_tags',
                        'generated_value': tags, 'confidence_score': 0.7,
                        'context_used': json.dumps({'similar_count': len(similar_orgs)}),
                        'prompt_version': self.qwen.prompt_version
                    })

                # Donate URL: only attempt if none exists yet, gated through
                # the proven score_confidence()/identity_match() logic —
                # below-threshold candidates are flagged for human review,
                # never written as the live donate_url.
                if not existing_donate_url:
                    donate_candidate = self.qwen.generate_website(
                        {**org_data, 'name': f"{name} donate"}, similar_orgs
                    )
                    if donate_candidate:
                        page_text = website_result['content_text'] if website_result else ''
                        level, ratio = identity_match(name, page_text)
                        factors = {
                            'found_on_official_website': bool(website_result),
                            'nonprofit_name_visible': level in ('exact', 'strong'),
                        }
                        confidence = score_confidence(factors)
                        if confidence >= 65:
                            results.append({
                                'org_ein': ein, 'enrichment_type': 'donate_url',
                                'generated_value': donate_candidate, 'confidence_score': confidence / 100.0,
                                'context_used': json.dumps({'identity_level': level}),
                                'prompt_version': self.qwen.prompt_version
                            })
                        else:
                            results.append({
                                'org_ein': ein, 'enrichment_type': 'donate_url_review',
                                'generated_value': donate_candidate, 'confidence_score': confidence / 100.0,
                                'context_used': json.dumps({'identity_level': level}),
                                'prompt_version': self.qwen.prompt_version
                            })
            except Exception as e:
                logger.error(f"Failed to enrich org {ein}: {e}")
                continue

        return results
```

Replace `_write_results()` with a version that also calls the new promotion step:

```python
    def _write_results(self, results: list) -> None:
        cursor = self.db.cursor()
        for result in results:
            cursor.execute(
                """INSERT INTO enrichment_run
                   (run_date, org_ein, enrichment_type, generated_value, confidence_score, context_used, prompt_version)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(date.today()), result['org_ein'], result['enrichment_type'],
                    result['generated_value'], result['confidence_score'], result['context_used'],
                    result.get('prompt_version', 'v1.0')
                )
            )
        self.db.commit()
        self._promote_to_registry(results)

    def _promote_to_registry(self, results: list) -> None:
        """Write passing enrichment results directly to registry_enriched.

        This closes the gap where the previous build wrote only to the
        enrichment_run staging table, which nothing else ever read from —
        nothing it produced was ever visible on daanaa.org. Each org's
        promotion is independent (one failure doesn't affect others), and
        never overwrites existing data with a lower-confidence guess:
        cause_tags/website/mission only promote when the corresponding
        registry_enriched field is currently empty/weak; donate_url only
        promotes above the confidence threshold, otherwise flags human_review.
        """
        cursor = self.db.cursor()
        for result in results:
            try:
                ein = result['org_ein']
                etype = result['enrichment_type']
                value = result['generated_value']

                if etype == 'cause_tags':
                    cursor.execute(
                        "UPDATE registry_enriched SET cause_tags = ? WHERE EIN = ? AND (cause_tags IS NULL OR cause_tags = '')",
                        (value, ein)
                    )
                elif etype == 'website':
                    cursor.execute(
                        "UPDATE registry_enriched SET website = ? WHERE EIN = ? AND (website IS NULL OR website = '')",
                        (value, ein)
                    )
                elif etype == 'volunteer_url':
                    cursor.execute(
                        "UPDATE registry_enriched SET volunteer_url = ? WHERE EIN = ?",
                        (value, ein)
                    )
                elif etype == 'mission':
                    context = json.loads(result.get('context_used') or '{}')
                    mission_source = context.get('mission_source', 'ai_web_grounded')
                    cursor.execute(
                        "UPDATE registry_enriched SET mission = ?, mission_source = ? WHERE EIN = ?",
                        (value, mission_source, ein)
                    )
                elif etype == 'donate_url':
                    cursor.execute(
                        "UPDATE registry_enriched SET donate_url = ?, donate_confidence = ?, donate_human_review = 0 WHERE EIN = ? AND (donate_url IS NULL OR donate_url = '')",
                        (value, result['confidence_score'], ein)
                    )
                elif etype == 'donate_url_review':
                    cursor.execute(
                        "UPDATE registry_enriched SET donate_human_review = 1, donate_confidence = ? WHERE EIN = ? AND (donate_url IS NULL OR donate_url = '')",
                        (result['confidence_score'], ein)
                    )
            except Exception as e:
                logger.error(f"Failed to promote {result.get('enrichment_type')} for org {result.get('org_ein')}: {e}")
                continue
        self.db.commit()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_enrich_batch_integration.py -v
```

Expected: all pass, including the 4 new tests in `TestConsolidatedEnrichment`

- [ ] **Step 5: Run the full existing suite to confirm no regressions**

```bash
pytest tests/test_enrich_batch.py tests/test_fixtures.py tests/test_semantic_lookup.py tests/test_qwen_inference.py tests/test_quality_measurement.py tests/test_prompt_improvement.py tests/test_enrich_batch_integration.py tests/test_cron_scripts.py tests/test_monitor_batch.py tests/test_donate_confidence.py tests/test_website_content.py -v
```

Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add scripts/enrich_batch.py tests/test_enrich_batch_integration.py
git commit -m "feat: wire website-grounded generation + inline promotion into EnrichmentBatch

_enrich_layer() now sequences: website candidate -> validate+fetch ->
grounded mission (if validated) -> tags informed by grounding -> donate_url
gated through score_confidence()/identity_match(). _promote_to_registry()
closes the gap where the prior build's output never reached
registry_enriched — promotion is per-field, never overwrites existing
good data, and donate_url below threshold flags donate_human_review=1
instead of writing an unverified link."
```

---

### Task 7: End-to-end integration test with realistic data

**Files:**
- Test: `tests/test_enrich_batch_integration.py` (append)

**Interfaces:**
- Consumes: everything from Tasks 1-6

- [ ] **Step 1: Write a comprehensive end-to-end test**

```python
# Append to tests/test_enrich_batch_integration.py

class TestFullConsolidatedFlow:
    """One realistic org through the entire sequenced pipeline, verifying
    every stage's output lands correctly — this is the test that would have
    caught 'nothing promotes to registry_enriched' if it had existed before
    the original 10-task build shipped."""

    def test_realistic_org_full_flow(self, test_db, mock_embeddings, enrich_config):
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO registry_enriched
            (EIN, organization_name, NTEE1, CITY, STATE, mission, mission_source,
             cause_tags, website, donate_url, donate_human_review)
            VALUES ('123456789', 'Riverside Youth Robotics', 'B25', 'Portland', 'OR',
                    'Provides educational services in Portland, OR.', 'ai_ntee',
                    '', '', NULL, NULL)
        """)
        test_db.commit()

        fake_website = {
            'url': 'https://riversideyouthrobotics.org',
            'content_text': (
                'Riverside Youth Robotics runs free after-school robotics '
                'and coding clubs for 6th-8th graders across three Portland '
                'middle schools, serving 150 students per year.'
            ),
            'identity_level': 'exact',
            'identity_ratio': 1.0,
            'volunteer_url': 'https://riversideyouthrobotics.org/volunteer',
        }

        def realistic_qwen(prompt: str, max_tokens: int = 200) -> str:
            if 'website' in prompt.lower() and 'donate' not in prompt.lower():
                return 'riversideyouthrobotics.org'
            if 'donate' in prompt.lower():
                return 'riversideyouthrobotics.org/donate'
            if 'robotics and coding clubs' in prompt.lower() or 'saturday' in prompt.lower() or 'middle schools' in prompt.lower():
                return 'Runs free after-school robotics and coding clubs for 150 middle schoolers across three Portland schools.'
            if 'tags' in prompt.lower():
                return 'Youth Development, STEM Education, Robotics'
            return 'generic response'

        from scripts.enrich_batch import EnrichmentBatch

        with patch('scripts.enrich_batch.validate_and_fetch_website', return_value=fake_website):
            batch = EnrichmentBatch(
                db_con=test_db, qwen_fn=realistic_qwen, embeddings_fn=mock_embeddings,
                config=enrich_config
            )
            stats = batch.run(dry_run=False, max_orgs=1)

        cursor.execute("""
            SELECT mission, mission_source, cause_tags, website, volunteer_url,
                   donate_url, donate_human_review, donate_confidence
            FROM registry_enriched WHERE EIN = '123456789'
        """)
        row = cursor.fetchone()
        mission, mission_source, cause_tags, website, volunteer_url, donate_url, donate_review, donate_conf = row

        # Mission was regenerated and grounded — no longer the generic template
        assert mission != 'Provides educational services in Portland, OR.'
        assert 'robotics' in mission.lower() or 'coding' in mission.lower()
        assert mission_source == 'ai_web_grounded'

        # Website was validated and promoted
        assert website == 'https://riversideyouthrobotics.org'

        # Volunteer page was captured, even though nothing displays it yet
        assert volunteer_url == 'https://riversideyouthrobotics.org/volunteer'

        # Cause tags were generated
        assert cause_tags

        # Donate URL: with found_on_official_website + exact identity match,
        # confidence clears 65 threshold, so it's live (or under review — the
        # test just needs to confirm ONE of these two consistent states,
        # not silently written with no evidence trail either way)
        assert (donate_url is not None) or (donate_review == 1)
        assert donate_conf is not None

        # Sanity on stats
        assert stats['orgs_processed'] > 0
        assert not stats['dry_run']
```

- [ ] **Step 2: Run test to verify it passes** (this is validating existing wiring, not new code — should already pass if Tasks 1-6 are correctly implemented)

```bash
pytest tests/test_enrich_batch_integration.py::TestFullConsolidatedFlow -v
```

Expected: PASS. If it fails, the failure points to an integration gap between
Tasks 1-6 that unit tests alone didn't catch — fix the actual wiring in
`scripts/enrich_batch.py`, do not weaken this test's assertions to make it pass.

- [ ] **Step 3: Commit**

```bash
git add tests/test_enrich_batch_integration.py
git commit -m "test: end-to-end integration test for the full consolidated flow

One realistic org traced through website validation -> grounded
mission -> informed tags -> donate_url gating -> promotion, verifying
every field actually lands in registry_enriched correctly. This is
the test that would have caught the original build's promotion gap."
```

---

### Task 8: Extend `monitor_batch.py` for per-field-type throughput

**Files:**
- Modify: `scripts/monitor_batch.py`
- Test: `tests/test_monitor_batch.py` (append)

**Interfaces:**
- Produces: `check_batch_health()` return dict gains a new key `'by_type'`: `Dict[str, int]` mapping enrichment_type to count for the checked date

- [ ] **Step 1: Write failing test**

```python
# Append to tests/test_monitor_batch.py

def test_check_batch_health_includes_per_type_breakdown(test_db):
    from datetime import date
    from scripts.monitor_batch import check_batch_health

    today = str(date.today())
    cursor = test_db.cursor()
    cursor.execute("""
        INSERT INTO enrichment_run
        (run_date, org_ein, enrichment_type, generated_value, confidence_score, prompt_version)
        VALUES
        (?, '111', 'cause_tags', 'Education', 0.7, 'v1.0'),
        (?, '111', 'mission', 'Some mission', 0.85, 'v1.0'),
        (?, '222', 'cause_tags', 'Health', 0.7, 'v1.0'),
        (?, '222', 'website', 'example.org', 0.9, 'v1.0')
    """, (today, today, today, today))
    test_db.commit()

    health = check_batch_health(test_db, check_date=today)

    assert health['by_type'] == {'cause_tags': 2, 'mission': 1, 'website': 1}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_monitor_batch.py::test_check_batch_health_includes_per_type_breakdown -v
```

Expected: FAIL with `KeyError: 'by_type'`

- [ ] **Step 3: Add the breakdown query to `check_batch_health()` in `scripts/monitor_batch.py`**

Add this block right after the existing `enrichment_count`/`batch_ran` calculation
(after the line `batch_ran = enrichment_count > 0`), and add `'by_type': by_type` to
the returned dict:

```python
    cursor.execute(
        "SELECT enrichment_type, COUNT(*) FROM enrichment_run WHERE run_date = ? GROUP BY enrichment_type",
        (check_date,)
    )
    by_type = {row[0]: row[1] for row in cursor.fetchall()}
```

Update the `return` statement to include it:

```python
    return {
        'batch_ran': batch_ran,
        'enrichment_count': enrichment_count,
        'checked_date': check_date,
        'quality_avg': quality_avg,
        'quality_trend': quality_trend,
        'by_type': by_type
    }
```

Update `main()`'s human-readable printout to show the breakdown:

```python
    if health['batch_ran']:
        print(f"✓ Batch ran: {health['enrichment_count']} enrichments")
        for etype, count in sorted(health['by_type'].items()):
            print(f"    {etype}: {count:,}")
    else:
        print(f"⚠ Batch MISSING ({checked_date})")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_monitor_batch.py -v
```

Expected: all pass, including the new test

- [ ] **Step 5: Commit**

```bash
git add scripts/monitor_batch.py tests/test_monitor_batch.py
git commit -m "feat: per-enrichment-type breakdown in monitor_batch.py

check_batch_health() now returns 'by_type' — a count per enrichment_type
for the checked date. This is what the 3-hourly monitoring cron (Task 9)
uses to see whether any one field type (mission, cause_tags, website,
donate_url) is lagging relative to the others during the backlog clear."
```

---

### Task 9: Cron scheduling — pause old script, exclusive backlog-clear mode

**Files:**
- Modify: `scripts/gpu_night.sh`
- Modify: `scripts/cron_enrich_nightly.sh`

**Interfaces:**
- No new Python interfaces — this is operational/shell scripting only

- [ ] **Step 1: Pause the `enrich_cause_tags_llm.py` block in `gpu_night.sh`**

In `scripts/gpu_night.sh`'s `start()` function, comment out the cause-tag enrichment
block (matching the exact commenting style already used for the 2026-06-22
website-discovery pause, so it's easy to find and re-enable later):

```bash
  # Cause tag enrichment: PAUSED 2026-07-07 for validation week — retired in
  # favor of the consolidated enrichment pipeline (scripts/enrich_batch.py),
  # which generates cause tags + mission + website + donate_url together
  # with shared context. Re-enable this block if quality_log shows the new
  # pipeline's tag accuracy regresses vs this script's baseline. See
  # DECISIONS.md 2026-07-07 and docs/superpowers/specs/2026-07-07-*.
  # if pgrep -f "scripts/enrich_cause_tags_llm.py" >/dev/null; then
  #   echo "[$(ts)] start: cause-tag enrichment already running — skipping"
  # else
  #   echo "[$(ts)] start: launching LLM cause-tag enrichment (249K gap)"
  #   nohup "$BASE/venv/bin/python3" "$BASE/scripts/enrich_cause_tags_llm.py" \
  #     >> "$LOG_DIR/cause_tags_llm.log" 2>&1 &
  # fi
```

Also comment out the corresponding `pkill` line in `stop()`:

```bash
  # echo "[$(ts)] stop: halting LLM cause-tag enrichment"
  # pkill -f "scripts/enrich_cause_tags_llm.py" 2>/dev/null
```

- [ ] **Step 2: Add an exclusive-access mode flag to `gpu_night.sh`'s `start()`**

Add a new function `start_exclusive()` alongside `start()` for use during the initial
backlog-clear period — this skips launching mission-gen and reembed_watchdog so
`enrich_batch.py` has the GPU to itself:

```bash
start_exclusive() {
  echo "[$(ts)] start_exclusive: launching embed_server only (mission-gen/reembed paused for backlog clear)"
  bash "$BASE/scripts/embed_server.sh" start

  if pgrep -f "llama-server.*--port ${PORT}" >/dev/null; then
    echo "[$(ts)] start_exclusive: llama-server already running — skipping"
  else
    echo "[$(ts)] start_exclusive: launching llama-server $(basename "$MODEL")"
    nohup "$SERVER_BIN" -m "$MODEL" --device Vulkan1 -ngl 99 -fa 1 \
      --parallel 6 --ctx-size 24576 --cont-batching \
      --port "$PORT" --host 127.0.0.1 --jinja \
      > "$SERVER_LOG" 2>&1 &
    for _ in $(seq 1 60); do
      grep -q "server is listening\|all slots are idle" "$SERVER_LOG" 2>/dev/null && break
      sleep 3
    done
  fi
  echo "[$(ts)] start_exclusive: done — mission-gen and reembed_watchdog intentionally NOT launched"
}
```

Add `start_exclusive` to the `case` statement at the bottom:

```bash
case "${1:-}" in
  start)              start ;;
  start_exclusive)    start_exclusive ;;
  stop)               stop ;;
  stop_embed_server)  stop_embed_server ;;
  *) echo "usage: $0 {start|start_exclusive|stop|stop_embed_server}" >&2; exit 1 ;;
esac
```

- [ ] **Step 3: Update `scripts/cron_enrich_nightly.sh` for exclusive-access mode**

Read the existing file first, then update the invocation to call
`gpu_night.sh start_exclusive` before running `enrich_batch.py`, and `gpu_night.sh stop`
after (which still runs the FTS-rebuild and FULL cleanup, including stopping
llama-server so the normal 9am handoff to mission-gen/reembed on subsequent nights
remains correct once backlog-clear mode ends):

```bash
#!/bin/bash
# Nightly enrichment batch — exclusive GPU access during initial backlog clear.
# Cron: 0 20 * * * /home/akbar/meritgiving/scripts/cron_enrich_nightly.sh

BASE_DIR="/home/akbar/meritgiving"
LOG_FILE="$BASE_DIR/logs/enrich_batch_$(date +'%Y%m%d').log"
VENV="$BASE_DIR/venv/bin/python3"

{
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] Starting enrichment batch (exclusive GPU mode)"

  cd "$BASE_DIR"
  bash scripts/gpu_night.sh start_exclusive

  source venv/bin/activate
  $VENV scripts/enrich_batch.py --workers 4 --batch-size 20

  if [ $? -eq 0 ]; then
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] Enrichment batch completed"
  else
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] Enrichment batch FAILED"
  fi

} >> "$LOG_FILE" 2>&1
```

Note: the existing `0 9 * * * gpu_night.sh stop` cron entry (already installed,
per Task 8 of the prior plan) continues to run at 9am regardless — it stops
llama-server, rebuilds FTS, and is what enforces the "stop at 9am" checkpoint
behavior. No new stop-side cron entry is needed.

- [ ] **Step 4: Verify shell syntax**

```bash
bash -n scripts/gpu_night.sh
bash -n scripts/cron_enrich_nightly.sh
```

Expected: both exit 0, no output (valid syntax)

- [ ] **Step 5: Confirm the live crontab is untouched by this task**

```bash
crontab -l | wc -l
```

Record the count. This task modifies script *contents* that an already-installed
cron entry calls — it does NOT run `crontab -e` or change the crontab itself.
Installing the updated scheduling (or switching from `start_exclusive` back to
`start` once the backlog is cleared) remains a manual operator decision, consistent
with the "never touch the live crontab autonomously" pattern established in the
prior plan's Task 8.

- [ ] **Step 6: Commit**

```bash
git add scripts/gpu_night.sh scripts/cron_enrich_nightly.sh
git commit -m "feat: exclusive-GPU backlog-clear mode + pause old cause-tags cron

gpu_night.sh gains start_exclusive (embed_server + llama-server only,
no mission-gen/reembed) for use during the initial 1.7M-org backlog
clear. enrich_cause_tags_llm.py's block is paused (commented, not
deleted) for a validation week per the consolidation design — same
reversible pattern used for the 2026-06-22 website-discovery pause.
Live crontab unchanged; switching modes remains a manual operator step."
```

---

## Self-Review

**1. Spec coverage:** All 9 items from the design doc are covered — donate_confidence
extraction (Task 1), website validation+fetch+volunteer detection (Task 2), grounded
mission generation (Task 3), extended tag generation (Task 4), volunteer_url schema
(Task 5), full wiring + inline promotion (Task 6), end-to-end validation (Task 7),
monitoring extension (Task 8), cron scheduling (Task 9). The prior plan's promotion
gap is directly addressed in Task 6/7.

**2. Placeholder scan:** No TBD/TODO markers; every step has complete code, not
descriptions of code.

**3. Type consistency:** `validate_and_fetch_website()` return shape (`dict` with
`url`, `content_text`, `identity_level`, `identity_ratio`, `volunteer_url` keys) is
used identically in Tasks 2, 6, and 7. `generate_mission_from_website()` and the
extended `generate_tags(..., grounding_context=)` signatures match between Tasks
3/4's definitions and Task 6's call sites. `score_confidence()`/`identity_match()`
signatures match between Task 1's extraction and Task 6's usage.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-07-enrichment-consolidation-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration — same pattern as the prior 10-task build, which caught a production-blocking bug and two real test-quality issues through this exact process.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
