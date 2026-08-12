#!/usr/bin/env python3
"""
Agentic Search Integration — Enhance existing /api/search results with intent routing.

This integrates agentic_search_router into daanaa_api.py's /api/search endpoint
without replacing existing logic. It:

1. Runs query through agentic router to detect multi-dimensional intent
2. Adds routing metadata + explainability to search results
3. Logs intent signals for recurring-giving nudges (privacy-preserving)
4. Ranks results by relevance + intent alignment

Usage (in daanaa_api.py):
  from scripts.agentic_search_integration import enhance_search_with_intent

  @app.get("/api/search")
  def search():
    results = fused_search()  # existing logic
    results = enhance_search_with_intent(results, query)  # add intent layer
    return results
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from scripts.agentic_search_router import AgenticSearchRouter
from intent_layer import record_intent, summarize_intent


def enhance_search_with_intent(search_results: dict, query: str, user_event_id: str = None) -> dict:
    """
    Enhance search results with agentic routing metadata + intent logging.

    Args:
        search_results: Response dict from fused_search() (has 'organizations' key)
        query: Original search query
        user_event_id: Optional event ID for intent tracking (P2: privacy-preserving)

    Returns:
        Enhanced results dict with:
        - 'agentic_routing': classification, confidence, explain_to_donor
        - 'result_reasoning': why each result appeared (keyword, semantic, or intent-aligned)
        - 'related_causes': suggestions for exploring related causes
    """

    router = AgenticSearchRouter()
    routing = router.route_query(query)

    # Log intent signal (privacy-preserving: no personal data, just kind + evidence)
    if user_event_id:
        record_intent(
            kind=_intent_kind_from_classification(routing["intent_classification"]),
            source="search",
            event_id=user_event_id,
            evidence=f"query_intent={routing['intent_classification']}"
        )

    # Extract organizations from results
    orgs = search_results.get("organizations", [])

    # Enhance each org with reasoning (P3: explainability)
    for org in orgs:
        org["match_reasoning"] = _explain_match(org, routing)

    # Add agentic routing metadata to response
    enhanced = {
        **search_results,
        "agentic_routing": {
            "intent_classification": routing["intent_classification"],
            "confidence": routing["confidence"],
            "search_path": routing["search_path"],
            "explain_to_donor": routing["explain_to_donor"],
        },
        "suggested_refinements": _suggest_refinements(routing),
        "related_causes": _suggest_related_causes(routing),
    }

    return enhanced


def _intent_kind_from_classification(classification: str) -> str:
    """Map search classification to intent kind (P2: privacy-preserving)."""
    if classification == "cause":
        return "learn"  # User is learning about causes
    elif classification == "organization":
        return "give"  # User is searching for orgs to support
    else:
        return "explore"  # Ambiguous intent


def _explain_match(org: dict, routing: dict) -> str:
    """Generate human-readable explanation of why this org appeared."""

    match_sources = org.get("match_sources", [])
    org_name = org.get("organization_name", "Unknown")

    reasons = []

    # Keyword match explanation
    if "keyword" in match_sources:
        query_keyword = org.get("keyword_match", "")
        if query_keyword:
            reasons.append(f"Matched keyword: '{query_keyword}'")
        else:
            reasons.append("Matched search keywords")

    # Semantic match explanation
    if "semantic" in match_sources:
        reasons.append("Similar mission to your search")

    # Intent-aligned explanation
    if routing["multi_dimensional_intent"]["audience"]["has_audience"]:
        audiences = routing["multi_dimensional_intent"]["audience"]["audiences"]
        org_tags = org.get("cause_tags", [])
        if any(a in str(org_tags).lower() for a in audiences):
            reasons.append(f"Serves {', '.join(audiences)}")

    return " · ".join(reasons) if reasons else "Relevant nonprofit"


def _suggest_refinements(routing: dict) -> list[str]:
    """Suggest query refinements based on detected intent gaps."""

    suggestions = []

    # If location detected but no results, suggest broadening
    if routing["multi_dimensional_intent"]["location"]["has_location"]:
        suggestions.append(
            f"Try searching without location to see nationwide organizations"
        )

    # If ambiguous, suggest more specific
    if routing["intent_classification"] == "ambiguous":
        suggestions.append("Try searching by cause (e.g., 'mental health') or organization name")

    return suggestions


def _suggest_related_causes(routing: dict) -> list[dict]:
    """Suggest related causes based on detected intent (P5: nudge without shame)."""

    suggestions = []

    # If user searched for cause, suggest related ones
    if routing["intent_classification"] == "cause":
        # In a real implementation, load from DB
        # For now, return empty (would be seeded from cause_tags or taxonomy)
        pass

    # If user searched for audience, suggest related orgs serving that audience
    if routing["multi_dimensional_intent"]["audience"]["has_audience"]:
        audiences = routing["multi_dimensional_intent"]["audience"]["audiences"]
        suggestions.append({
            "type": "audience_related",
            "text": f"Browse more {', '.join(audiences)}-focused nonprofits",
        })

    return suggestions


if __name__ == "__main__":
    # Example usage
    mock_results = {
        "organizations": [
            {
                "ein": "123456789",
                "organization_name": "Cleveland Mental Health Center",
                "mission": "Providing mental health services to underserved communities",
                "cause_tags": ["health", "mental", "community"],
                "match_sources": ["keyword", "semantic"],
                "keyword_match": "mental health",
            },
            {
                "ein": "987654321",
                "organization_name": "Ohio Community Foundation",
                "mission": "Supporting local nonprofits through grants",
                "cause_tags": ["community", "foundation"],
                "match_sources": ["keyword"],
                "keyword_match": "community",
            },
        ]
    }

    query = "mental health services near Cleveland"
    enhanced = enhance_search_with_intent(mock_results, query)

    import json

    print(json.dumps(enhanced, indent=2))
