"""Tests for scripts/website_normalize.normalize_website — written failing-first.

Canonical form: bare lowercase host[/path]; https:// is dropped (it is the
default every consumer already applies), http:// is kept (signal that the
site may be http-only); trailing slash stripped at root; malformed schemes
repaired; values with no real domain return None.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from website_normalize import normalize_website  # noqa: E402


def test_https_dropped_to_bare():
    assert normalize_website("https://www.example.org") == "www.example.org"
    assert normalize_website("https://example.org/") == "example.org"


def test_http_kept():
    assert normalize_website("http://example.org") == "http://example.org"
    assert normalize_website("http://example.org/") == "http://example.org"


def test_caps_lowered_host_only():
    assert normalize_website("WWW.NORTHWOODTECH.EDU/FOUNDATION") == \
        "www.northwoodtech.edu/FOUNDATION"  # path case preserved
    assert normalize_website("HTTPS://EXAMPLE.ORG") == "example.org"


def test_bare_passthrough():
    assert normalize_website("example.org") == "example.org"
    assert normalize_website("maidenrock.org/mraca") == "maidenrock.org/mraca"


def test_trailing_slash_root_only():
    assert normalize_website("example.org/") == "example.org"
    # non-root paths keep their trailing slash (some routers require it)
    assert normalize_website("https://districtseven.altrusa.org/oshkosh/") == \
        "districtseven.altrusa.org/oshkosh/"


def test_query_preserved():
    assert normalize_website("https://example.org/page?id=2") == \
        "example.org/page?id=2"


def test_malformed_schemes_repaired():
    assert normalize_website("HTTPS:WWW.TAMARACKHEALTH.ORG") == "www.tamarackhealth.org"
    assert normalize_website("https:/www.avhrrc.org") == "www.avhrrc.org"
    assert normalize_website("https//thelifeinbloomfoundation.org/") == \
        "thelifeinbloomfoundation.org"
    assert normalize_website("https//:archtaxfoundation.org") == "archtaxfoundation.org"
    assert normalize_website("https.//www.projectoutrageouslove.org/") == \
        "www.projectoutrageouslove.org"
    assert normalize_website("https:/.llbef.weebly.com") == "llbef.weebly.com"
    assert normalize_website("http//www.iaswm.org/") == "http://www.iaswm.org"


def test_scheme_typos_repaired():
    # real typo families from IRS-sourced data — all mean https
    assert normalize_website("httpw://spcycling.org") == "spcycling.org"
    assert normalize_website("htpps://www.raisewithus.org") == "www.raisewithus.org"
    assert normalize_website("htttps://www.ohioal-anon.org") == "www.ohioal-anon.org"
    assert normalize_website("Htttp://HomefrontHugs.org") == "homefronthugs.org"
    assert normalize_website("ttps://www.eatondc.org/page.html") == \
        "www.eatondc.org/page.html"
    assert normalize_website("htt://www.example.com") == "www.example.com"
    assert normalize_website("htpp://freefarmsand.org") == "freefarmsand.org"
    assert normalize_website("hhttps://jerseysforjack.org/") == "jerseysforjack.org"
    assert normalize_website("hhtps://pamagic.org") == "pamagic.org"
    # scheme-less lookalikes must NOT be eaten: tps.org is a real domain shape
    assert normalize_website("tps.org") == "tps.org"
    assert normalize_website("https.org") == "https.org"


def test_semicolon_doubled_and_prefixed_schemes():
    assert normalize_website("http;//www.bikealpharetta.org") == \
        "http://www.bikealpharetta.org"
    assert normalize_website("https;//www.help4homelessfamilies.org") == \
        "www.help4homelessfamilies.org"
    assert normalize_website("http://http://littlevillefair.com/") == \
        "http://littlevillefair.com"
    assert normalize_website("//https:www.gluedinc.org") == "www.gluedinc.org"
    assert normalize_website("https/bonnie.wixsite.com/x") == \
        "bonnie.wixsite.com/x"
    # "://" can never appear in a domain — any garbled token before it
    # is a scheme attempt, default https
    assert normalize_website("HPTTS://WWW.EXAMPLE.COM") == "www.example.com"
    assert normalize_website("HPS://CONNECT.CPASEA.ORG/") == "connect.cpasea.org"
    assert normalize_website("www://theopenresource.org") == "theopenresource.org"


def test_www_slash_repaired():
    assert normalize_website("www/classicdance.org") == "www.classicdance.org"
    assert normalize_website("WWW/VISIONOFHOPEMINISTRIES.ORG") == \
        "www.visionofhopeministries.org"
    assert normalize_website("HTTP://WWW/LSUS.EDU/FOUNDATION") == \
        "http://www.lsus.edu/FOUNDATION"


def test_junk_returns_none():
    assert normalize_website("") is None
    assert normalize_website(None) is None
    assert normalize_website("N/A") is None
    assert normalize_website("NONE") is None
    assert normalize_website("no website") is None
    assert normalize_website("localhost") is None  # no dot — not a public domain


def test_whitespace_trimmed():
    assert normalize_website("  example.org  ") == "example.org"


def test_idempotent():
    for raw in ("https://WWW.Example.ORG/Path/", "http//x.org", "example.org"):
        once = normalize_website(raw)
        assert normalize_website(once) == once


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)} tests passed")
