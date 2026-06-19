"""Deterministic reply templates per route.

V1 keeps these template-based — no LLM in the loop. That makes the agent:
- Predictable (no hallucination on sensitive channels like legal@/security@)
- Available 24/7 (no GPU or external API dependency)
- Auditable (you can read the template, not a model)

When Anthropic credits land or local-llama capacity is reliable in daytime,
a Drafter v2 can replace these with model-generated replies for HIGH-tier
channels only, keeping LOW-tier human-written.
"""

from __future__ import annotations

from scripts.email_agent.routing import Route

AI_FOOTER = (
    "\n\n— Daanaa\n"
    "(This acknowledgement is automated. A human reviews anything involving "
    "your data, legal, or verification. Reply and a person will pick it up.)"
)


def reply_template(route: Route, sender_first_name: str | None) -> tuple[str, str]:
    """Return (subject_prefix, body) for the auto-acknowledgement."""
    greet = f"Hi {sender_first_name}," if sender_first_name else "Hi,"

    bodies = {
        "support": (
            f"{greet}\n\nThanks for reaching out to Daanaa. We read every message and "
            "respond within 1–2 business days.\n\n"
            "A few common questions we can address quickly:\n"
            "  • To find a nonprofit: daanaa.org/directory\n"
            "  • To add your organization: daanaa.org/for-nonprofits\n"
            "  • To report a data issue: trust@daanaa.org\n\n"
            "If you're writing about something else, a real person will pick this up shortly."
        ),
        "hello": (
            f"{greet}\n\nThanks for writing to Daanaa. We read every email — "
            "someone will come back to you within a couple of working days.\n\n"
            "If your question is about a specific organization, the fastest path "
            "is to include the EIN (9 digits, e.g. 12-3456789) so we can pull up "
            "the right record."
        ),
        "orgs": (
            f"{greet}\n\nThanks for reaching out about your organization's page on Daanaa.\n\n"
            "To verify and claim your page, we send a short verification letter to the "
            "address the IRS has on file (the one shown on your 990). It usually arrives in "
            "3–5 business days. Reply with your EIN and we'll start the process.\n\n"
            "If you've already received the letter, the page to enter your PIN is "
            "https://daanaa.org/verify."
        ),
        "partners": (
            f"{greet}\n\nThanks for the partnership note. Daanaa is a small, founder-run "
            "platform focused on making the 1.8M nonprofits in IRS data findable. We're "
            "selective about partnerships — please share a couple of sentences about what "
            "you have in mind and we'll respond within a week."
        ),
        "contact": (
            f"{greet}\n\nThis address receives messages from webmasters and operators whose "
            "sites our pipeline has crawled. Daanaa's crawler identifies itself as "
            "`Daanaa-DataBot/1.0 (contact@daanaa.org)` and respects robots.txt.\n\n"
            "If you'd like us to slow the crawl rate, exclude a path, or remove cached "
            "data, reply with the domain and we'll address it within a couple of working days."
        ),
        "trust": (
            f"{greet}\n\nThank you for flagging this. Reporting data issues is how Daanaa "
            "keeps the public record honest, and it's a core part of how we operate.\n\n"
            "We've logged your report and a human will review it. If the underlying record "
            "is from the IRS filing (revenue, name, NTEE), corrections often need to happen "
            "with the IRS first; we'll pick those up on the next refresh. For things we can "
            "fix directly (a wrong donate link, a bad AI-generated mission, a mismatched "
            "website), expect a response within a couple of working days."
        ),
        "verify": (
            f"{greet}\n\nThanks for writing about org verification. Verification at Daanaa is "
            "human-reviewed — a team member will pick this up and walk you through the steps "
            "within a couple of working days.\n\n"
            "If you have documents to share (board letter, IRS determination letter, official "
            "site that confirms your role), feel free to attach them in your next reply."
        ),
        "privacy": (
            f"{greet}\n\nThanks for your privacy or data request. We take this seriously — "
            "Daanaa stores no donor accounts and no donor IP addresses, and a person reviews "
            "every privacy request individually rather than handling it automatically.\n\n"
            "A human will respond within 30 days, in line with applicable privacy law. If you "
            "can include the specific request (access, deletion, correction) and any "
            "identifier we'd need to act on it, that will speed things up."
        ),
        "legal": (
            f"{greet}\n\nThank you for your legal notice. Daanaa takes all legal "
            "correspondence seriously and a person — not an automated system — handles it. "
            "Expect a response within a couple of working days.\n\n"
            "For takedown or correction requests, please include: the specific URL or EIN at "
            "issue, the nature of the concern, and your relationship to the organization."
        ),
        "security": (
            f"{greet}\n\nThank you for the security report. We treat security disclosures as "
            "a priority. A human will review your report and respond within a couple of "
            "working days.\n\n"
            "If you haven't already, please don't share the details publicly until we've had "
            "a chance to assess and patch. We don't have a paid bounty program yet, but we'll "
            "credit researchers who report responsibly."
        ),
    }
    return ("Re:", bodies.get(route.address.split("@")[0], bodies["hello"]) + AI_FOOTER)


def extract_first_name(from_header: str) -> str | None:
    """Best-effort: pull a first name from a 'Name <email>' From header."""
    if not from_header or "<" not in from_header:
        return None
    name = from_header.split("<", 1)[0].strip().strip('"').strip()
    if not name or "@" in name:
        return None
    first = name.split()[0] if name.split() else None
    return first if first and first.replace("-", "").replace(".", "").isalpha() else None
