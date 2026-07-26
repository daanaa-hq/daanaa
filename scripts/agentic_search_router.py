#!/usr/bin/env python3
"""
Agentic Search Router — Intent-aware query decomposition and multi-path search.

Builds on existing infrastructure:
- search_intent_classifier: cause vs. org classification
- semantic_search / fts: multi-vector search endpoints
- intent_layer: privacy-preserving intent tracking
- org_embeddings: fresh vectors for semantic search

Goal: Answer "find nonprofits beyond their names" by decomposing intent,
routing to optimal search paths, and surfacing results with explainable reasoning.

Usage:
  python3 scripts/agentic_search_router.py --test
  python3 scripts/agentic_search_router.py --decompose "mental health near Cleveland"
"""

import json
import sqlite3
from pathlib import Path
from typing import Literal
import sys
import os

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.search_intent_classifier import SearchIntentClassifier

REPO_ROOT = Path(__file__).parent.parent
DB = REPO_ROOT / "data" / "merit_registry.db"

class AgenticSearchRouter:
    """
    Routes queries to optimal search paths based on intent decomposition.

    Routing logic:
    1. Classify intent (cause, org, ambiguous) via search_intent_classifier
    2. Detect location intent if present (e.g., "near Cleveland", "in Ohio")
    3. Detect audience intent if present (e.g., "for youth", "small nonprofits")
    4. Route to semantic or FTS based on classification
    5. Apply filters (location, size, etc.)
    6. Log intent signal for recurring-giving nudges
    """

    def __init__(self, db_path=DB):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.classifier = SearchIntentClassifier(db_path)

        # Common location keywords
        self.location_keywords = {
            "near", "around", "city", "county", "state", "area",
            "Cleveland", "New York", "Los Angeles", "Chicago", "Texas",
            "California", "Ohio", "Pennsylvania", "Illinois",
            "OH", "NY", "CA", "TX", "PA", "IL", "CO", "WA", "MA", "MN"
        }

        # Common audience keywords
        self.audience_keywords = {
            "youth", "young", "teen", "elderly", "senior", "kids", "children",
            "women", "men", "immigrant", "refugee", "lgbtq", "disabled",
            "veterans", "homeless", "low-income", "underserved"
        }

        # Size keywords
        self.size_keywords = {
            "small": "micro",
            "tiny": "micro",
            "big": "established",
            "large": "established",
            "major": "established",
            "local": "professional",
        }

    def extract_location_intent(self, query: str) -> dict:
        """Extract location from query if present."""
        import re
        query_lower = query.lower()
        location = None

        # First, look for explicit location indicators followed by a place
        location_indicators = ["near", "around", "in", "by", "within"]
        for indicator in location_indicators:
            pattern = rf'{indicator}\s+([a-z\s]+?)(?:\s+(?:for|with|services|nonprofits|organizations|facility|facilities)|\s*$)'
            match = re.search(pattern, query_lower)
            if match:
                location = match.group(1).strip()
                # Filter out non-location words
                if location.split()[0] not in ['for', 'with', 'to', 'at']:
                    break
                location = None

        # If no explicit location found, check for standalone place names with word boundaries
        if not location:
            for kw in self.location_keywords:
                if len(kw) <= 2:  # State abbreviations
                    pattern = rf'\b{re.escape(kw.lower())}\b'
                    if re.search(pattern, query_lower):
                        location = kw
                        break

        return {
            "has_location": location is not None,
            "location": location,
            "reason": f"Detected location in query" if location else None
        }

    def extract_audience_intent(self, query: str) -> dict:
        """Extract target audience from query if present."""
        query_lower = query.lower()
        audiences = []

        for kw in self.audience_keywords:
            if kw.lower() in query_lower:
                audiences.append(kw.lower())

        return {
            "has_audience": len(audiences) > 0,
            "audiences": list(set(audiences)),  # dedupe
            "reason": f"Detected audience keywords: {', '.join(audiences)}" if audiences else None
        }

    def extract_size_intent(self, query: str) -> dict:
        """Extract org size preference from query if present."""
        query_lower = query.lower()
        size = None

        for kw, size_band in self.size_keywords.items():
            if kw.lower() in query_lower:
                size = size_band
                break

        return {
            "has_size": size is not None,
            "size": size,
            "reason": f"Detected size keyword suggesting '{size}' orgs" if size else None
        }

    def route_query(self, query: str) -> dict:
        """Main routing logic: classify intent + decompose query."""

        # Step 1: Classify base intent (cause vs. org vs. ambiguous)
        classification = self.classifier.classify(query)

        # Step 2: Extract multi-dimensional intent
        location_intent = self.extract_location_intent(query)
        audience_intent = self.extract_audience_intent(query)
        size_intent = self.extract_size_intent(query)

        # Step 3: Decide search path
        search_path = classification["suggested_path"]
        if location_intent["has_location"] or audience_intent["has_audience"]:
            # Multi-dimensional search: start with semantic, then filter
            search_path = "semantic_with_filters"

        # Step 4: Build routing decision
        routing = {
            "query": query,
            "intent_classification": classification["intent"],
            "confidence": classification["confidence"],
            "search_path": search_path,
            "multi_dimensional_intent": {
                "location": location_intent,
                "audience": audience_intent,
                "size": size_intent,
            },
            "reasoning": f"Query intent: {classification['intent']} ({classification['reason']}). "
                        f"Search path: {search_path}. "
                        f"Filters: {', '.join(filter(None, [location_intent['reason'], audience_intent['reason'], size_intent['reason']]))}",
            "explain_to_donor": self._human_explain(classification, location_intent, audience_intent, size_intent)
        }

        return routing

    def _human_explain(self, classification, location_intent, audience_intent, size_intent) -> str:
        """Generate human-readable explanation of search logic (P3: evidence-based)."""
        parts = []

        # Explain base classification
        if classification["intent"] == "cause":
            parts.append("🎯 Searching by cause area")
        elif classification["intent"] == "organization":
            parts.append("🏢 Searching by organization name")
        else:
            parts.append("🔍 Searching both causes and organization names")

        # Explain dimensional filters
        if location_intent["has_location"]:
            parts.append(f"📍 Near {location_intent['location']}")
        if audience_intent["has_audience"]:
            parts.append(f"👥 Serving {', '.join(audience_intent['audiences'])}")
        if size_intent["has_size"]:
            parts.append(f"📊 {size_intent['size'].title()} organizations")

        return " · ".join(parts)

    def test_queries(self):
        """Test routing on sample queries."""
        test_cases = [
            "mental health services",
            "Cleveland Foundation",
            "youth employment near Columbus",
            "small food banks in Texas",
            "education nonprofits for immigrant families",
            "elderly care facilities",
        ]

        print("\nAgentic Search Router — Routing Tests")
        print("=" * 80)

        for query in test_cases:
            result = self.route_query(query)
            print(f"\nQuery: {query}")
            print(f"Intent: {result['intent_classification']} (conf={result['confidence']:.2f})")
            print(f"Path: {result['search_path']}")
            print(f"Explain: {result['explain_to_donor']}")
            print("-" * 80)

if __name__ == "__main__":
    router = AgenticSearchRouter()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            router.test_queries()
        elif sys.argv[1] == "--decompose" and len(sys.argv) > 2:
            query = " ".join(sys.argv[2:])
            result = router.route_query(query)
            print(json.dumps(result, indent=2))
        else:
            print(__doc__)
            sys.exit(1)
    else:
        print(__doc__)
