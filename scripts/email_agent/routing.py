"""Address → department + autonomy mapping.

Source of truth in meritgiving-ops/email-agent-routing.md. Keep in sync.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

Tier = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class Route:
    address: str
    department: str
    role: str
    tier: Tier


ROUTES: dict[str, Route] = {
    "hello":    Route("hello@daanaa.org",    "04-operations",           "Front desk",                 "high"),
    "orgs":     Route("orgs@daanaa.org",     "10-nonprofit-success",    "Nonprofit relations",        "high"),
    "partners": Route("partners@daanaa.org", "07-people-partnerships",  "Partnerships",               "high"),
    "contact":  Route("contact@daanaa.org",  "02-data-research",        "Crawler/webmaster contact",  "high"),
    "trust":    Route("trust@daanaa.org",    "02-data-research",        "Data-correction intake",     "medium"),
    "verify":   Route("verify@daanaa.org",   "10-nonprofit-success",    "Org verification",           "low"),
    "privacy":  Route("privacy@daanaa.org",  "06-legal-compliance",     "Privacy / data requests",    "low"),
    "legal":    Route("legal@daanaa.org",    "06-legal-compliance",     "Legal / takedowns",          "low"),
    "security": Route("security@daanaa.org", "01-product-eng",          "Vulnerability disclosure",   "low"),
}

_ADDR_RE = re.compile(r"<?([\w.+-]+)@([\w.-]+)>?", re.I)


def classify(headers: dict[str, str]) -> Route | None:
    """Pick a Route by inspecting Delivered-To / To / Cc headers.

    Delivered-To wins because Google Groups forwarding preserves it as the
    canonical "this is the alias the sender targeted" header even when
    To: contains something else (e.g. a list rewrite).
    """
    for header_name in ("Delivered-To", "To", "Cc"):
        raw = headers.get(header_name, "")
        for match in _ADDR_RE.finditer(raw):
            local, domain = match.group(1).lower(), match.group(2).lower()
            if domain != "daanaa.org":
                continue
            if local in ROUTES:
                return ROUTES[local]
    return None
