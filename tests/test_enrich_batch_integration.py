"""Task 7: Integration tests for the enrichment batch orchestrator.

Tests EnrichmentBatch, which wires together SemanticLookup (Task 3),
QwenInference (Task 4), QualityMeasurement (Task 5), and PromptImprovement
(Task 6) into the nightly batch entry point.

Both tests deliberately insert only the 2 orgs under test into test_db's
registry_enriched table, with empty cause_tags/website. That makes the
enrichment outcome fully deterministic:

- Both orgs need enrichment (empty cause_tags AND empty website), so the
  orchestrator's SELECT ... LIMIT 2 picks up exactly these 2 rows.
- Since no OTHER org in the table has non-empty cause_tags/website,
  SemanticLookup.find_similar_orgs() always returns [] for both orgs (its
  candidate query requires cause_tags/website to be populated) - so the
  Qwen prompts always fall back to the "no similar orgs" template text.
- The mock_qwen fixture returns a non-empty string for ANY prompt
  containing "tags" (cause-tags prompts always do, via the config
  template's "cause tags" phrase) and ANY prompt containing "domain"
  (website prompts always do, via "Suggest the most likely domain name").
  So generate_tags()/generate_website() succeed for every org, every time.

That means for 2 input orgs we get EXACTLY 2 cause_tags results + 2 website
results = 4 total enrichment results, with no randomness left to hide a bug
behind a loose ">= 0" assertion.
"""
import sqlite3

from scripts.enrich_batch import EnrichmentBatch


def _insert_org_needing_enrichment(test_db, org):
    """Insert a sample org with cause_tags/website cleared to '' so it is
    picked up by EnrichmentBatch's "needs enrichment" WHERE clause.
    """
    cursor = test_db.cursor()
    cursor.execute(
        """INSERT INTO registry_enriched
           (EIN, organization_name, NTEE1, mission, city, state, cause_tags, website)
           VALUES (?, ?, ?, ?, ?, ?, '', '')""",
        (
            org['ein'], org['organization_name'], org['ntee1'],
            org['mission'], org['city'], org['state'],
        )
    )
    test_db.commit()


class TestEnrichBatchIntegration:
    """Integration tests exercising the full 4-layer enrichment cycle."""

    def test_enrich_batch_end_to_end(self, test_db, mock_qwen, mock_embeddings, sample_orgs, enrich_config):
        """Full cycle: 2 orgs needing enrichment -> real, deterministic stats.

        Both sample orgs are inserted with cause_tags/website cleared, so
        both are selected. Neither org has a peer with non-empty
        cause_tags/website, so semantic similarity always returns [] and
        the Qwen prompts always take the "no similar orgs" fallback path -
        which mock_qwen still answers with a non-empty string for both the
        cause_tags prompt (contains "tags") and the website prompt
        (contains "domain"). So exactly 2 tags + 2 websites are generated.
        """
        for org in sample_orgs[:2]:
            _insert_org_needing_enrichment(test_db, org)

        batch = EnrichmentBatch(
            db_con=test_db, qwen_fn=mock_qwen, embeddings_fn=mock_embeddings,
            config=enrich_config
        )

        stats = batch.run(dry_run=True, max_orgs=2)

        assert stats['orgs_processed'] == 4, (
            "orgs_processed counts enrichment RESULTS (per the orchestrator's "
            "own definition: len(enrich_results)), not unique orgs - 2 orgs x "
            "(1 tags result + 1 website result) = 4"
        )
        assert stats['tags_generated'] == 2
        assert stats['websites_generated'] == 2
        assert stats['dry_run'] is True
        assert isinstance(stats['elapsed_seconds'], float)
        assert stats['elapsed_seconds'] >= 0

    def test_enrich_batch_respects_dry_run(self, test_db, mock_qwen, mock_embeddings, sample_orgs, enrich_config):
        """dry_run=True must never write to enrichment_run, verified by a
        direct DB query (not by inference from the returned stats dict).
        """
        for org in sample_orgs[:2]:
            _insert_org_needing_enrichment(test_db, org)

        batch = EnrichmentBatch(
            db_con=test_db, qwen_fn=mock_qwen, embeddings_fn=mock_embeddings,
            config=enrich_config
        )

        stats = batch.run(dry_run=True, max_orgs=2)

        # Sanity: the run still did real work (otherwise a 0-write count
        # would be trivially true for the wrong reason - no work happened).
        assert stats['orgs_processed'] == 4

        cursor = test_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM enrichment_run")
        count = cursor.fetchone()[0]
        assert count == 0, "dry_run=True must not write any rows to enrichment_run"
