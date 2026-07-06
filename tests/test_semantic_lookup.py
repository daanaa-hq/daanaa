"""Task 3: Tests for semantic similarity lookup.

Tests the SemanticLookup class that finds similar nonprofits by embedding
cosine similarity.
"""

import pytest


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
        enabling the context-aware generation in Task 4.
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
        results = lookup.find_similar_orgs('611234567', count=5)

        # Verify cause_tags present
        assert len(results) > 0
        for result in results:
            # cause_tags should be present (even if empty string for null)
            assert 'cause_tags' in result
            # At least some results should have non-empty cause_tags
            if result['cause_tags']:
                assert isinstance(result['cause_tags'], str)

    def test_similarity_score_ranking(self, test_db, mock_embeddings, sample_orgs):
        """Test that results are ranked by similarity score in descending order.

        This verifies that the similarity scoring and sorting mechanism works
        correctly: results should be sorted from highest to lowest similarity score.
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

        # Query for similar orgs to the tech education org
        lookup = SemanticLookup(test_db, mock_embeddings)
        results = lookup.find_similar_orgs('111111111', count=10)

        # Should have at least 1 result
        assert len(results) >= 1

        # Verify results are sorted by similarity score in descending order
        similarity_scores = [r['similarity_score'] for r in results]
        for i in range(len(similarity_scores) - 1):
            assert similarity_scores[i] >= similarity_scores[i + 1], \
                f"Results should be sorted by similarity in descending order. " \
                f"Got scores: {similarity_scores}"

        # Verify all results have valid similarity scores
        for result in results:
            assert 0.0 <= result['similarity_score'] <= 1.0, \
                f"Similarity score should be between 0.0 and 1.0, got {result['similarity_score']}"
