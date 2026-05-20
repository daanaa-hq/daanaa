"""MERIT org scorer — stub.

Wraps the existing merit_scorer_v3_3.py logic for the new platform.
Full implementation comes in Phase 0, Week 3 data sprint.

See SKILL.md: .claude/skills/badge-scoring/SKILL.md
"""

from typing import Optional


BADGE_TIERS = {
    "exceptional": (90, 100),
    "high": (75, 89),
    "solid": (60, 74),
    "developing": (40, 59),
    "needs_data": (0, 39),
}


def badge_from_score(score: Optional[float]) -> str:
    if score is None:
        return "needs_data"
    for tier, (low, high) in BADGE_TIERS.items():
        if low <= score <= high:
            return tier
    return "needs_data"


def score_org(org: dict) -> Optional[float]:
    """Score a single org dict. Returns 0-100 or None if insufficient data.

    TODO: port merit_scorer_v3_3.py logic here.
    Current canonical scorer lives at: /home/akbar/meritgiving/api/merit_scorer_v3_3.py
    """
    raise NotImplementedError(
        "Port merit_scorer_v3_3.py to this package before calling score_org(). "
        "See .claude/skills/badge-scoring/SKILL.md for the migration plan."
    )
