#!/usr/bin/env python3
"""
Semantic lookup: find similar orgs using embeddings.
"""
import sqlite3
import json
from typing import Callable, Optional
from pathlib import Path

class SemanticLookup:
    """Find similar orgs using semantic similarity on embeddings."""

    def __init__(
        self,
        db_con: sqlite3.Connection,
        embeddings_fn: Callable,
        embeddings_port: int = 11436
    ):
        """
        Args:
            db_con: SQLite connection with registry_enriched table
            embeddings_fn: Function to generate embeddings: embeddings_fn(texts: list) -> list[list[float]]
            embeddings_port: Port for embeddings server (for future direct calls)
        """
        self.db = db_con
        self.embeddings_fn = embeddings_fn
        self.embeddings_port = embeddings_port
        self._embedding_cache = {}  # Cache org embeddings in memory

    def find_similar_orgs(
        self,
        org_ein: str,
        count: int = 5,
        similarity_threshold: float = 0.0
    ) -> list[dict]:
        """
        Find similar orgs by semantic similarity.

        Args:
            org_ein: EIN of query org
            count: Number of similar orgs to return
            similarity_threshold: Minimum cosine similarity (0.0-1.0)

        Returns:
            List of dicts with keys: EIN, organization_name, mission, cause_tags,
                                     website, similarity_score
        """
        cursor = self.db.cursor()
        cursor.execute(
            """SELECT organization_name, mission, NTEE1 FROM registry_enriched
               WHERE EIN = ?""",
            (org_ein,)
        )
        row = cursor.fetchone()
        if not row:
            return []

        query_name, query_mission, query_ntee = row

        try:
            query_embedding = self.embeddings_fn([query_mission])[0]
        except Exception as e:
            print(f"Error embedding org {org_ein}: {e}")
            return []

        cursor.execute(
            """SELECT EIN, organization_name, mission, cause_tags, website
               FROM registry_enriched
               WHERE EIN != ? AND (cause_tags IS NOT NULL AND cause_tags != ''
                                   OR website IS NOT NULL AND website != '')
               LIMIT 5000""",
            (org_ein,)
        )
        candidate_orgs = cursor.fetchall()

        if not candidate_orgs:
            return []

        missions = [org[2] for org in candidate_orgs]
        try:
            embeddings = self.embeddings_fn(missions)
        except Exception as e:
            print(f"Error embedding candidates: {e}")
            return []

        def cosine_sim(a, b):
            import math
            dot = sum(x * y for x, y in zip(a, b))
            mag_a = math.sqrt(sum(x**2 for x in a))
            mag_b = math.sqrt(sum(x**2 for x in b))
            if mag_a == 0 or mag_b == 0:
                return 0.0
            return dot / (mag_a * mag_b)

        similarities = []
        for i, (ein, name, mission, tags, website) in enumerate(candidate_orgs):
            sim = cosine_sim(query_embedding, embeddings[i])
            if sim >= similarity_threshold:
                similarities.append({
                    'EIN': ein,
                    'organization_name': name,
                    'mission': mission,
                    'cause_tags': tags or '',
                    'website': website or '',
                    'similarity_score': sim
                })

        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similarities[:count]
