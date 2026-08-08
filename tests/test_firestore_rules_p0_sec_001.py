"""P0-SEC-001 — regression guard for Firestore nonprofit-verification rules.

WHAT THIS DOES AND DOES NOT PROVE
---------------------------------
This is a STATIC test. It parses firestore.rules and asserts the
nonprofit_verifications match block denies client access. It does NOT evaluate
the rules against a live Firestore instance.

Real authorization testing needs the Firebase emulator
(@firebase/rules-unit-testing + a Java runtime), which is not installed in this
repo. Those tests are written in tests/firestore_rules/ and are NOT yet
executed. Do not report P0-SEC-001 as behaviourally verified until they run.

What this guard does catch, and why it is worth having: the original defect was
a single permissive line (`allow read, write: if request.auth.uid != null`)
granting every authenticated user read/write over every nonprofit's records.
This test fails if that line — or any other client-permissive grant — returns to
this block. It runs with no dependencies, so it works in any CI we happen to have.

Run: python3 -m pytest tests/test_firestore_rules_p0_sec_001.py -v
"""
import re
from pathlib import Path

RULES = Path(__file__).resolve().parents[1] / "firestore.rules"


def _block(collection: str) -> str:
    """Return the body of the match block for a top-level collection."""
    text = RULES.read_text()
    start = text.find(f"match /{collection}/")
    assert start != -1, f"no match block for /{collection}/ in firestore.rules"
    # The opening brace is the LAST '{' on the match line -- earlier ones are
    # path wildcards like {nonprofit_id} and {document=**}, not block braces.
    line_end = text.index("\n", start)
    depth, i = 0, text.rindex("{", start, line_end)
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i : j + 1]
    raise AssertionError("unbalanced braces in firestore.rules")


def _grants(block: str):
    """Every `allow ...: if <condition>;` condition in a block."""
    return [c.strip() for c in re.findall(r"allow[^:]*:\s*if\s+([^;]+);", block)]


def test_rules_file_exists():
    assert RULES.exists(), f"missing {RULES}"


def test_nonprofit_verifications_denies_all_client_access():
    """The P0-SEC-001 fix: client reads and writes are denied outright."""
    grants = _grants(_block("nonprofit_verifications"))
    assert grants, "no allow rule found — block may have been removed entirely"
    for cond in grants:
        assert cond == "false", (
            f"nonprofit_verifications grants client access on condition {cond!r}. "
            "All legitimate access is server-side via the Firebase Admin SDK, "
            "which bypasses rules. See P0-SEC-001."
        )


def test_nonprofit_verifications_rejects_the_original_defect():
    """Guard the exact regression: any-authenticated-user access."""
    block = _block("nonprofit_verifications")
    normalised = re.sub(r"\s+", " ", block)
    assert "request.auth.uid != null" not in normalised, (
        "the original P0-SEC-001 defect has returned: this granted every "
        "authenticated user read/write over every nonprofit's records"
    )


def test_wildcard_subtree_is_covered():
    """The block must still cover the {document=**} subtree, not just the root.

    Narrowing the path while denying the root would leave nested documents
    governed by some other (or no) rule.
    """
    text = RULES.read_text()
    assert "match /nonprofit_verifications/{nonprofit_id}/{document=**}" in text, (
        "the nonprofit_verifications match path changed; a deny on a narrower "
        "path can leave nested documents ungoverned"
    )


def test_unrelated_wallet_rules_unchanged():
    """Scope guard: P0-SEC-001 must not alter user wallet authorization."""
    text = RULES.read_text()
    for coll in (
        "saved_organizations",
        "funded_log",
        "volunteer_hour_logs",
        "volunteer_hour_confirmations",
        "consent_records",
    ):
        assert f"match /{{uid}}/{coll}/{{document=**}}" in text, f"{coll} rule missing"
    # Wallet collections stay owner-scoped.
    owner_scoped = text.count("request.auth.uid == uid")
    assert owner_scoped >= 6, (
        f"expected wallet + audit_log rules to remain owner-scoped, found "
        f"{owner_scoped} occurrences of request.auth.uid == uid"
    )


def test_audit_logs_remain_write_denied():
    """Audit logs stay backend-write-only."""
    block = _block("{uid}")  # first {uid} block; audit_logs checked textually
    assert block is not None
    text = re.sub(r"\s+", " ", RULES.read_text())
    assert "allow write: if false;" in text, "audit_logs write-deny was removed"
