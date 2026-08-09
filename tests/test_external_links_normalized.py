"""Regression: raw hrefs on website/donate_url/volunteer_url fields.

THE BUG (reported by a live user 2026-08-08)
---------------------------------------------
Websites are stored as bare domains ("www.example.org"). Rendering that value
directly as `href={org.website}` makes the browser resolve it as a RELATIVE
path -- a visitor clicking "Visit website" on /org/<ein> landed on
/org/<ein>/www.example.org instead of the org's actual site.

frontend/src/utils/externalLink.ts::normalizeExternalUrl() exists to fix this
(prepends https://, and rejects javascript:/data: schemes -- so the raw value
was also a live XSS surface, not only a broken link). The first fix only
covered the files a narrow grep happened to find (OrgInfoHierarchy, OrgCard,
WalletCard, GiveYourWayRouter); a broader sweep later found 21 raw hrefs
across 13 MORE files, including OrganizationDetail.tsx -- the exact page the
user reported.

THIS TEST
---------
A static source scan, not a rendered-DOM test, so it catches the pattern
everywhere at once rather than one file at a time as bug reports arrive.
Verified (see history) to fail against every file before its fix and pass
after. Any new `href={x.website}`-shaped JSX anywhere in frontend/src is
exactly the bug this guards.
"""
import pathlib
import re

FRONTEND_SRC = pathlib.Path(__file__).resolve().parents[1] / "frontend" / "src"

# Matches href={<expr>.website|website_url|donate_url|volunteer_url[.value]}
# NOT already wrapped in normalizeExternalUrl(...).
RAW_HREF = re.compile(
    r"href=\{(?!normalizeExternalUrl)"
    r"(?:[A-Za-z_$][\w$?.]*\.)?"
    r"(?:website|website_url|donate_url|volunteer_url)(?:\.value)?"
    r"\}"
)


def _tsx_files():
    return [
        f for f in FRONTEND_SRC.rglob("*.tsx")
        if "__tests__" not in f.parts and "node_modules" not in f.parts
    ]


def test_frontend_src_has_tsx_files():
    """Guard the premise: if the tree moves, this test must be revisited."""
    assert _tsx_files(), f"no .tsx files found under {FRONTEND_SRC}"


def test_no_raw_external_href():
    """Every website/donate_url/volunteer_url href must go through normalizeExternalUrl.

    Fails exactly the way the original bug did: a bare `href={org.website}` (or
    donate_url / volunteer_url / *_url.value) resolves as a relative path in the
    browser and can carry a javascript:/data: scheme unfiltered.
    """
    offenders = {}
    for f in _tsx_files():
        matches = RAW_HREF.findall(f.read_text())
        if matches:
            offenders[str(f.relative_to(FRONTEND_SRC.parent))] = matches

    assert not offenders, (
        "raw (unnormalized) external href(s) found -- these resolve as RELATIVE "
        "paths in the browser and bypass the javascript:/data: scheme filter:\n"
        + "\n".join(f"  {f}: {m}" for f, m in offenders.items())
    )
