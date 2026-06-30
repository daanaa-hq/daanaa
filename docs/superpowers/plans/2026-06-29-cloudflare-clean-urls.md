# Cloudflare Clean URLs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish extensionless Cloudflare Pages URLs consistently in overlay canonicals, sitemaps, structured data, text discovery files, and internal links.

**Architecture:** Keep physical source files in `visibility/public` unchanged. Add one Cloudflare-specific normalization pass to `prepare_cloudflare_pages.py` that rewrites URL references only in the copied deployable tree.

**Tech Stack:** Python 3 standard library, `unittest`, Cloudflare Pages.

---

### Task 1: Define the URL policy

**Files:**
- Create: `visibility/tests/test_prepare_cloudflare_pages.py`
- Modify: `visibility/scripts/prepare_cloudflare_pages.py`

- [ ] **Step 1: Write the failing unit test**

```python
from visibility.scripts.prepare_cloudflare_pages import normalize_overlay_urls

self.assertEqual(
    normalize_overlay_urls(
        '<link rel="canonical" href="https://data.daanaa.org/guides/index.html">'
    ),
    '<link rel="canonical" href="https://data.daanaa.org/guides/">',
)
self.assertEqual(
    normalize_overlay_urls('<a href="/guides/give.html">Give</a>'),
    '<a href="/guides/give">Give</a>',
)
```

- [ ] **Step 2: Verify the test fails**

Run: `python3 -m unittest visibility.tests.test_prepare_cloudflare_pages -v`

Expected: FAIL because `normalize_overlay_urls` does not exist.

- [ ] **Step 3: Implement the minimal URL normalizer**

```python
def clean_html_path(path: str) -> str:
    if path.endswith("/index.html"):
        return path[: -len("index.html")]
    return path[:-5]


def normalize_overlay_urls(text: str) -> str:
    text = ABSOLUTE_HTML_URL_RE.sub(replace_absolute_url, text)
    return ROOT_HTML_LINK_RE.sub(replace_root_link, text)
```

The regexes must preserve query strings and fragments and must match only
`data.daanaa.org` absolute URLs or root-relative HTML link attributes.

- [ ] **Step 4: Verify the focused tests pass**

Run: `python3 -m unittest visibility.tests.test_prepare_cloudflare_pages -v`

Expected: PASS.

### Task 2: Normalize the deployable tree

**Files:**
- Modify: `visibility/scripts/prepare_cloudflare_pages.py`
- Modify: `visibility/tests/test_prepare_cloudflare_pages.py`

- [ ] **Step 1: Write the failing integration test**

```python
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "page.html").write_text(
        '<link rel="canonical" href="https://data.daanaa.org/page.html">'
    )
    (root / "pages.xml").write_text(
        "<loc>https://data.daanaa.org/page.html</loc>"
    )
    normalize_deployable_urls(root)
    self.assertIn(
        "https://data.daanaa.org/page",
        (root / "pages.xml").read_text(),
    )
```

- [ ] **Step 2: Verify the integration test fails**

Run: `python3 -m unittest visibility.tests.test_prepare_cloudflare_pages -v`

Expected: FAIL because `normalize_deployable_urls` does not exist.

- [ ] **Step 3: Implement deployable-tree traversal**

```python
def normalize_deployable_urls(root: Path = OUT) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        original = path.read_text(encoding="utf-8")
        normalized = normalize_overlay_urls(original)
        if normalized != original:
            path.write_text(normalized, encoding="utf-8")
```

Call this after `rewrite_text_files(chunks)` and before `validate_sizes()`.

- [ ] **Step 4: Run all visibility tests**

Run: `python3 -m unittest discover -s visibility/tests -v`

Expected: all tests pass.

### Task 3: Build, deploy, and verify

**Files:**
- Generated: `visibility/public/**`
- Generated: `visibility/cloudflare-public/**`

- [ ] **Step 1: Regenerate the overlay**

Run: `python3 visibility/scripts/build_overlay.py`

Expected: overlay validation succeeds.

- [ ] **Step 2: Run stewardship and prepare Cloudflare assets**

Run: `python3 visibility/scripts/check_content_stewardship.py`

Run: `python3 visibility/scripts/prepare_cloudflare_pages.py`

Expected: both commands exit 0.

- [ ] **Step 3: Verify generated URL consistency**

Run: `rg -n 'https://data\\.daanaa\\.org/[^[:space:]"<]*\\.html|(?:href|content)="/[^"?]*\\.html' visibility/cloudflare-public`

Expected: no matches.

- [ ] **Step 4: Deploy only Cloudflare Pages**

Run: `DEPLOY=1 PROJECT_NAME=daanaa-visibility BRANCH=main ./visibility/scripts/deploy_cloudflare_pages.sh`

Expected: Wrangler reports deployment complete.

- [ ] **Step 5: Verify production and notify search systems**

Check representative pages, every child sitemap, canonical targets, and
`robots.txt`. Then run `python3 visibility/scripts/submit_indexnow.py`.

Expected: representative final URLs return 200 without redirect; sitemap checks
pass; IndexNow reports successful submission.
