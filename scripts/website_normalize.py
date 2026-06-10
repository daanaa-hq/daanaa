"""Canonical form for the registry_enriched.website column.

One format, one function. Canonical = bare lowercase host[/path]:
  - https:// is dropped — it is the default every consumer already applies
    (frontend and donation pipeline both prepend it when absent)
  - http:// is KEPT — signal that the site may be http-only; forcing https
    on those would break the link
  - host is lowercased; path/query case is preserved (servers may care)
  - trailing slash stripped at the root only (deeper paths keep theirs)
  - malformed schemes (HTTPS:WWW., https:/, https//, http//, https.//)
    are repaired before parsing
  - values with no real dotted domain (N/A, NONE, localhost, prose) → None

Used by the one-time backfill and by every writer that touches `website`
(web_finder_agent, overnight_pipeline link intake, expand_990_coverage).
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

# Mangled scheme prefixes seen in IRS-sourced data, most-specific first.
# Captures whether the author meant http (no s) so we can preserve it.
# The separator MUST contain ':', ';', or '/' — otherwise https.org (a
# real domain shape) would be eaten as a mangled scheme. A bare '/' is
# safe here because "http/..." can never be a valid host anyway.
_BROKEN_SCHEME_RE = re.compile(
    r"^http(s?)(?:[:;][/.]*|[./]*//[:./]*|/)\s*", re.IGNORECASE
)

# Typo'd schemes (httpw, htpps, htttps, hhttps, hhtps, ttps, htt, htpp...).
# The separator MUST contain ':' or '//' — that is what distinguishes a
# mistyped scheme from a real short domain like tps.org or https.org.
_TYPO_SCHEME_RE = re.compile(
    r"^h{0,2}t{1,3}p{0,2}(s{0,2})w?(?::[/.]*|[./]*//)\s*", re.IGNORECASE
)

# Any other garbled token before "://" (HPTTS://, HPS://, www://...).
# "://" can never appear inside a host or path, so this is always a
# botched scheme attempt — strip it, default https.
_GARBLED_SCHEME_RE = re.compile(r"^[A-Za-z]{0,8}://\s*")

# "www/" where "www." was meant (also shows up after a stripped scheme).
_WWW_SLASH_RE = re.compile(r"^www/", re.IGNORECASE)

# Junk values that mean "no website" rather than a malformed one.
_JUNK_RE = re.compile(r"^(n/?a|none|no\s.*|-+|\.+)$", re.IGNORECASE)


def normalize_website(raw: str | None) -> str | None:
    """Return the canonical form of a website value, or None if it is junk."""
    if not raw:
        return None
    val = raw.strip()
    if not val or _JUNK_RE.match(val):
        return None

    # Separate a well-formed scheme; repair a mangled one. Looped to a
    # fixed point: handles doubled schemes ("http://http://x") and junk
    # prefixes before the scheme ("//https:x").
    scheme = "https"
    for _ in range(4):
        # Leading artifacts: dots/colons/slashes around broken schemes.
        val = val.lstrip("./:;")
        before = val
        low = val.lower()
        if low.startswith("https://"):
            val = val[8:]
        elif low.startswith("http://"):
            scheme, val = "http", val[7:]
        else:
            m = _BROKEN_SCHEME_RE.match(val)
            if m:
                if m.group(1) == "":  # exact "http", broken sep — keep it
                    scheme = "http"
                val = val[m.end():]
            else:
                # Misspelled scheme (httpw, htpps, ttps, ...). Intent is
                # too murky to trust the s — default to https.
                m = _TYPO_SCHEME_RE.match(val) or _GARBLED_SCHEME_RE.match(val)
                if m:
                    val = val[m.end():]
        if val == before:
            break
    if not val:
        return None

    # "www/" where "www." was meant.
    val = _WWW_SLASH_RE.sub("www.", val)

    # Split host from path/query; lowercase host only.
    parsed = urlparse(f"//{val}")
    host = (parsed.netloc or "").lower()
    rest = parsed.path or ""
    if parsed.query:
        rest += f"?{parsed.query}"
    if "." not in host:
        return None  # no dotted domain — localhost, prose, garbage

    if rest in ("", "/"):
        rest = ""  # trailing slash at root carries no meaning

    out = f"{host}{rest}"
    return f"http://{out}" if scheme == "http" else out
