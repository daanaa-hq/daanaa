"""Task 3: Tests for semantic similarity lookup.

Tests the SemanticLookup class that finds similar nonprofits by embedding
cosine similarity.
"""

import math

import pytest


def _cosine_sim(a, b):
    """Local, independent cosine similarity helper for test-side ground truth.

    Deliberately re-implemented here (rather than imported from
    scripts.semantic_lookup) so that the expected ranking in
    test_similarity_score_ranking is computed independently of the system
    under test's own math/sort, not merely re-derived from its output.
    """
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x**2 for x in a))
    mag_b = math.sqrt(sum(x**2 for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


class TestSemanticLookup:
    """Test suite for SemanticLookup class."""

    def test_basic_result_list(self, test_db, mock_embeddings, sample_orgs):
        """Test that find_similar_orgs returns a list of dicts with expected keys.

        For a query org with cause_tags and website, should return a list
        of similar orgs ranked by similarity score, each with keys:
        EIN, organization_name, mission, cause_tags, website, similarity_score
        """
        from scripts.semantic_lookup import SemanticLookup

        # Insert sample orgs
        cursor = test_db.cursor()
        for org in sample_orgs:
            cursor.execute(
                """INSERT INTO registry_enriched
                   (EIN, organization_name, NTEE1, mission, cause_tags, website)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (org['ein'], org['organization_name'], org['ntee1'],
                 org['mission'], org['cause_tags'], org['website'])
            )
        test_db.commit()

        # Create SemanticLookup and query
        lookup = SemanticLookup(test_db, mock_embeddings)
        results = lookup.find_similar_orgs('611234567', count=3)

        # Verify results structure
        assert isinstance(results, list)
        assert len(results) > 0
        assert len(results) <= 3

        # Check each result has expected keys
        for result in results:
            assert 'EIN' in result
            assert 'organization_name' in result
            assert 'mission' in result
            assert 'cause_tags' in result
            assert 'website' in result
            assert 'similarity_score' in result
            assert isinstance(result['similarity_score'], float)
            assert 0.0 <= result['similarity_score'] <= 1.0

    def test_org_not_found_returns_empty(self, test_db, mock_embeddings, sample_orgs):
        """Test that querying a non-existent org returns empty list.

        If the EIN does not exist in the database, should return [].
        """
        from scripts.semantic_lookup import SemanticLookup

        # Insert sample orgs
        cursor = test_db.cursor()
        for org in sample_orgs:
            cursor.execute(
                """INSERT INTO registry_enriched
                   (EIN, organization_name, NTEE1, mission, cause_tags, website)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (org['ein'], org['organization_name'], org['ntee1'],
                 org['mission'], org['cause_tags'], org['website'])
            )
        test_db.commit()

        # Create SemanticLookup and query with non-existent EIN
        lookup = SemanticLookup(test_db, mock_embeddings)
        results = lookup.find_similar_orgs('999999999', count=5)

        # Should return empty list
        assert results == []

    def test_excludes_self_from_results(self, test_db, mock_embeddings, sample_orgs):
        """Test that the query org itself is not included in results.

        If a query org is semantically similar to itself (which it always is),
        it should be filtered out from the results.
        """
        from scripts.semantic_lookup import SemanticLookup

        # Insert sample orgs
        cursor = test_db.cursor()
        for org in sample_orgs:
            cursor.execute(
                """INSERT INTO registry_enriched
                   (EIN, organization_name, NTEE1, mission, cause_tags, website)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (org['ein'], org['organization_name'], org['ntee1'],
                 org['mission'], org['cause_tags'], org['website'])
            )
        test_db.commit()

        # Create SemanticLookup and query
        lookup = SemanticLookup(test_db, mock_embeddings)
        results = lookup.find_similar_orgs('611234567', count=10)

        # Verify the query org (611234567) is not in results
        for result in results:
            assert result['EIN'] != '611234567', \
                "Query org should not appear in similar orgs results"

    def test_includes_cause_tags_in_context(self, test_db, mock_embeddings, sample_orgs):
        """Test that returned orgs include cause_tags as context.

        The cause_tags should be included in the result for each similar org,
        enabling the context-aware generation in Task 4. This asserts against
        a specific known cause_tags value on a specific candidate org, rather
        than a conditional check that can pass vacuously if cause_tags never
        comes through correctly.
        """
        from scripts.semantic_lookup import SemanticLookup

        # Insert sample orgs
        cursor = test_db.cursor()
        for org in sample_orgs:
            cursor.execute(
                """INSERT INTO registry_enriched
                   (EIN, organization_name, NTEE1, mission, cause_tags, website)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (org['ein'], org['organization_name'], org['ntee1'],
                 org['mission'], org['cause_tags'], org['website'])
            )

        # Add a candidate org with a specific, known non-empty cause_tags
        # value that we assert on directly below.
        known_cause_tags = 'Education,Mentorship'
        cursor.execute(
            """INSERT INTO registry_enriched
               (EIN, organization_name, NTEE1, mission, cause_tags, website)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ('671789012', 'Youth Mentorship Collective', 'O',
             'Pairs volunteer mentors with at-risk youth for tutoring and guidance',
             known_cause_tags, 'youthmentorship.org')
        )
        test_db.commit()

        # Create SemanticLookup and query. similarity_threshold is set below
        # zero so this test never depends on the sign of the mock's
        # pseudo-random cosine similarity for the known candidate — the
        # point here is verifying cause_tags pass-through, not filtering.
        lookup = SemanticLookup(test_db, mock_embeddings)
        results = lookup.find_similar_orgs('611234567', count=10, similarity_threshold=-1.0)

        # The known org must appear in results with its exact cause_tags intact.
        matching = [r for r in results if r['EIN'] == '671789012']
        assert len(matching) == 1, (
            "Expected candidate org 671789012 to appear in similar orgs results"
        )
        assert matching[0]['cause_tags'] == known_cause_tags, (
            f"Expected cause_tags {known_cause_tags!r} to pass through unchanged, "
            f"got {matching[0]['cause_tags']!r}"
        )

    def test_similarity_score_ranking(self, test_db, mock_embeddings, sample_orgs):
        """Test that results are ranked by similarity score in descending order,
        matching an independently-computed ground truth ordering.

        Rather than only checking that the returned scores happen to be
        non-increasing (which is guaranteed by find_similar_orgs's own
        `.sort(reverse=True)` regardless of whether the underlying similarity
        computation means anything), this test computes the expected ranking
        itself: it calls mock_embeddings directly to get vectors for the
        query mission and each candidate mission, computes cosine similarity
        locally via `_cosine_sim`, and asserts that SemanticLookup.find_similar_orgs
        returns EINs in that same independently-derived order.
        """
        from scripts.semantic_lookup import SemanticLookup

        # Create a custom set of orgs
        test_orgs = [
            {
                'ein': '111111111',
                'organization_name': 'Tech Education Foundation',
                'ntee1': 'T',
                'mission': 'Provides technology training and education programs',
                'cause_tags': '["Technology", "Education"]',
                'website': 'techfoundation.org'
            },
            {
                'ein': '222222222',
                'organization_name': 'Digital Skills Academy',
                'ntee1': 'T',
                'mission': 'Teaches programming and digital literacy skills',
                'cause_tags': '["Technology", "Education"]',
                'website': 'digitalacademy.org'
            },
            {
                'ein': '333333333',
                'organization_name': 'Animal Shelter Alliance',
                'ntee1': 'D',
                'mission': 'Rescues and cares for abandoned animals',
                'cause_tags': '["Animals"]',
                'website': 'animalshelter.org'
            },
            {
                'ein': '444444444',
                'organization_name': 'Healthcare Clinic',
                'ntee1': 'E',
                'mission': 'Provides medical services to underserved populations',
                'cause_tags': '["Health"]',
                'website': 'healthclinic.org'
            },
        ]

        cursor = test_db.cursor()
        for org in test_orgs:
            cursor.execute(
                """INSERT INTO registry_enriched
                   (EIN, organization_name, NTEE1, mission, cause_tags, website)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (org['ein'], org['organization_name'], org['ntee1'],
                 org['mission'], org['cause_tags'], org['website'])
            )
        test_db.commit()

        # --- Independently compute the expected ranking ---
        # Call mock_embeddings directly (not through SemanticLookup) to get
        # the query and candidate vectors, then compute cosine similarity
        # ourselves. This ground truth is derived without ever calling
        # find_similar_orgs, so it can't just be echoing the SUT's own sort.
        query_org = test_orgs[0]
        candidate_orgs = test_orgs[1:]

        query_vector = mock_embeddings([query_org['mission']])[0]
        candidate_vectors = mock_embeddings([org['mission'] for org in candidate_orgs])

        expected_ranking = sorted(
            (
                (org['ein'], _cosine_sim(query_vector, vec))
                for org, vec in zip(candidate_orgs, candidate_vectors)
            ),
            key=lambda pair: pair[1],
            reverse=True,
        )
        expected_ein_order = [ein for ein, _ in expected_ranking]

        # --- Compare against the system under test ---
        lookup = SemanticLookup(test_db, mock_embeddings)
        results = lookup.find_similar_orgs('111111111', count=10)

        assert len(results) == len(expected_ein_order), (
            f"Expected {len(expected_ein_order)} results, got {len(results)}"
        )

        actual_ein_order = [r['EIN'] for r in results]
        assert actual_ein_order == expected_ein_order, (
            "Returned EIN order should match the independently-computed "
            f"cosine similarity ranking. Expected {expected_ein_order}, "
            f"got {actual_ein_order}"
        )

        # Verify all results have valid similarity scores
        for result in results:
            assert 0.0 <= result['similarity_score'] <= 1.0, \
                f"Similarity score should be between 0.0 and 1.0, got {result['similarity_score']}"
