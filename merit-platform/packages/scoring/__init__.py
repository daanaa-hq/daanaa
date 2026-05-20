"""MERIT scoring engine.

Badge tiers (relative within NTEE peer group):
  90-100  Exceptional Impact
  75-89   High Impact
  60-74   Solid Performer
  40-59   Developing
  < 40    Needs Data

Canonical scorer: scorer.py
Do not import from legacy versions (v1, v2, v3.x).
"""

from .scorer import score_org, badge_from_score

__all__ = ["score_org", "badge_from_score"]
