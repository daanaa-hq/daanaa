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

Task 6 update: _enrich_layer() now validates every website candidate via
validate_and_fetch_website() (a real HTTP fetch) before counting it as
"found" - promoting an unvalidated LLM guess to a fact is exactly the
overconfident behavior that validation step exists to prevent (see Task 6
brief). Making a real network call from these tests would be slow and
environment-dependent (and near-certain to fail in a sandboxed test run
with no DNS), so the 3 pre-existing tests below patch
scripts.enrich_batch.validate_and_fetch_website to a deterministic
"always validates" stub - preserving their original "2 orgs -> 2 tags + 2
websites" arithmetic without hitting the network. _insert_org_needing_enrichment
also now seeds mission_source + donate_url with non-trigger placeholder
values, so the newer mission-regeneration and donate_url-discovery paths
(also added in Task 6) stay inert here and don't add extra, unasserted
result rows that would throw off the exact counts these tests check.
"""
import sqlite3
from unittest.mock import patch

from scripts.enrich_batch import EnrichmentBatch

# A deterministic "always validates" stand-in for validate_and_fetch_website,
# used by the pre-Task-6 tests below so they exercise real orchestration
# counts without making a real HTTP request. volunteer_url is deliberately
# None so it doesn't add an extra volunteer_url result to the counts these
# tests assert on.
_FAKE_VALIDATED_WEBSITE = {
    'url': 'https://example.org',
    'content_text': 'Generic placeholder website content.',
    'identity_level': 'strong',
    'identity_ratio': 0.7,
    'volunteer_url': None,
}


def _insert_org_needing_enrichment(test_db, org):
    """Insert a sample org with cause_tags/website cleared to '' so it is
    picked up by EnrichmentBatch's "needs enrichment" WHERE clause.

    mission_source is seeded to 'ai_generated' (not one of the
    mission-regeneration trigger values) and donate_url to a non-empty
    placeholder, so Task 6's mission-regeneration and donate_url-discovery
    branches are both inert for these orgs - keeping this fixture's
    contribution to each test limited to exactly cause_tags + website, as
    it was before Task 6 added those paths.
    """
    cursor = test_db.cursor()
    cursor.execute(
        """INSERT INTO registry_enriched
           (EIN, organization_name, NTEE1, mission, mission_source, city, state,
            cause_tags, website, donate_url)
           VALUES (?, ?, ?, ?, 'ai_generated', ?, ?, '', '', 'https://placeholder.example/donate')""",
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

        with patch('scripts.enrich_batch.validate_and_fetch_website', return_value=_FAKE_VALIDATED_WEBSITE):
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

        with patch('scripts.enrich_batch.validate_and_fetch_website', return_value=_FAKE_VALIDATED_WEBSITE):
            stats = batch.run(dry_run=True, max_orgs=2)

        # Sanity: the run still did real work (otherwise a 0-write count
        # would be trivially true for the wrong reason - no work happened).
        assert stats['orgs_processed'] == 4

        cursor = test_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM enrichment_run")
        count = cursor.fetchone()[0]
        assert count == 0, "dry_run=True must not write any rows to enrichment_run"

    def test_enrich_batch_survives_one_bad_org(
        self, test_db, mock_qwen, mock_embeddings, sample_orgs, enrich_config
    ):
        """Regression test: one org that blows up inside the per-org enrichment
        body must not abort the whole batch (final whole-branch review finding).

        Root cause this guards against: any per-org failure raising inside
        _enrich_layer's loop and killing every other org's results along with
        it - e.g. the NTEE NULL/empty crash (fixed separately in
        qwen_inference.py), or any other unexpected failure mode that might
        surface later. _enrich_layer now wraps the per-org body in a
        try/except that logs and continues, so this test injects a failure
        via self.qwen.generate_website directly (bypassing generate_website's
        own internal try/except entirely, the way an error in prompt-building
        or semantic lookup would) to prove the OUTER guard in _enrich_layer is
        what saves the run, not just generate_website's internal handling.

        Task 6 update: the per-org body now generates the website candidate
        BEFORE cause tags (website -> validate -> grounded mission -> tags ->
        donate_url), so the poison target moved from generate_tags to
        generate_website - it's now the first Qwen call in the loop, so
        poisoning it still guarantees zero partial results for the poisoned
        org (nothing has been appended to `results` yet when it raises).

        Two orgs are inserted; the first (EIN 611234567) is rigged to raise
        when generate_website is called for it - since the exception fires
        before that org contributes anything to `results`, per-org atomicity
        means NEITHER of its results survives. The second org behaves
        normally via mock_qwen and still produces its usual 2 results (1
        tags + 1 website, since validate_and_fetch_website is patched to
        always validate). The batch must not crash, and must not lose the
        healthy org's results because of the poisoned one.
        """
        for org in sample_orgs[:2]:
            _insert_org_needing_enrichment(test_db, org)

        poison_ein = sample_orgs[0]['ein']  # '611234567' (Tech for Good Foundation)

        batch = EnrichmentBatch(
            db_con=test_db, qwen_fn=mock_qwen, embeddings_fn=mock_embeddings,
            config=enrich_config
        )

        real_generate_website = batch.qwen.generate_website

        def flaky_generate_website(org_data, similar_orgs, max_retries=1):
            if org_data.get('EIN') == poison_ein:
                raise RuntimeError("simulated unexpected per-org failure")
            return real_generate_website(org_data, similar_orgs, max_retries)

        batch.qwen.generate_website = flaky_generate_website

        # Must complete without raising (this is the main assertion: a bad
        # org must not propagate an exception out of run()/_enrich_layer).
        with patch('scripts.enrich_batch.validate_and_fetch_website', return_value=_FAKE_VALIDATED_WEBSITE):
            stats = batch.run(dry_run=True, max_orgs=2)

        # Only the healthy org's 2 results (1 tags + 1 website) survive -
        # the poisoned org contributes 0 results, not partial/corrupt ones.
        assert stats['orgs_processed'] == 2
        assert stats['tags_generated'] == 1
        assert stats['websites_generated'] == 1

        # And dry_run still holds even on the failure path - no partial
        # writes from the poisoned org's aborted iteration.
        cursor = test_db.cursor()
        cursor.execute("SELECT COUNT(*) FROM enrichment_run")
        assert cursor.fetchone()[0] == 0


from unittest.mock import patch, MagicMock


class TestConsolidatedEnrichment:
    """Tests for Task 6: website validation -> grounded mission -> tags ->
    inline promotion, wired into EnrichmentBatch."""

    def test_promotion_writes_to_registry_enriched_directly(self, test_db, mock_qwen, mock_embeddings, enrich_config):
        """The core fix: previously nothing promoted enrichment_run rows
        into registry_enriched, so nothing was ever visible on daanaa.org.
        This confirms promotion actually happens for fields that don't
        require website validation (cause_tags is generated regardless of
        whether a website was found)."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO registry_enriched
            (EIN, organization_name, NTEE1, mission, cause_tags, website)
            VALUES ('999888777', 'Test Nonprofit', 'B', 'Old generic mission', '', '')
        """)
        test_db.commit()

        from scripts.enrich_batch import EnrichmentBatch

        # No website candidate validates in this test (website discovery is
        # mocked to return None) — cause_tags must still promote, since tag
        # generation doesn't depend on a validated website. website must NOT
        # promote: writing an unvalidated LLM guess as the org's official
        # site would be exactly the overconfident behavior Task 2's
        # validation step exists to prevent.
        with patch('scripts.enrich_batch.validate_and_fetch_website', return_value=None):
            batch = EnrichmentBatch(
                db_con=test_db, qwen_fn=mock_qwen, embeddings_fn=mock_embeddings,
                config=enrich_config
            )
            batch.run(dry_run=False, max_orgs=1)

        cursor.execute("SELECT cause_tags, website FROM registry_enriched WHERE EIN = ?", ('999888777',))
        cause_tags, website = cursor.fetchone()
        assert cause_tags        # non-empty, was promoted
        assert website in (None, '')  # NOT promoted — unvalidated guess must not become fact

    def test_grounded_mission_used_when_website_validates(self, test_db, mock_qwen, mock_embeddings, enrich_config):
        """When Task 2's validation succeeds, mission generation should use
        generate_mission_from_website() (grounded), not the NTEE fallback."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO registry_enriched
            (EIN, organization_name, NTEE1, mission, mission_source, cause_tags, website)
            VALUES ('888777666', 'Grounded Test Org', 'B', 'Generic old mission', 'ai_ntee', '', '')
        """)
        test_db.commit()

        fake_website_result = {
            'url': 'https://groundedtestorg.org',
            'content_text': 'We run a Saturday coding academy for 200 students.',
            'identity_level': 'exact',
            'identity_ratio': 1.0,
            'volunteer_url': 'https://groundedtestorg.org/volunteer',
        }

        from scripts.enrich_batch import EnrichmentBatch

        with patch('scripts.enrich_batch.validate_and_fetch_website', return_value=fake_website_result):
            batch = EnrichmentBatch(
                db_con=test_db, qwen_fn=mock_qwen, embeddings_fn=mock_embeddings,
                config=enrich_config
            )
            batch.run(dry_run=False, max_orgs=1)

        cursor.execute(
            "SELECT mission, mission_source, volunteer_url FROM registry_enriched WHERE EIN = ?",
            ('888777666',)
        )
        mission, mission_source, volunteer_url = cursor.fetchone()
        assert mission != 'Generic old mission'  # was regenerated
        assert mission_source == 'ai_web_grounded'
        assert volunteer_url == 'https://groundedtestorg.org/volunteer'

    def test_promotion_never_overwrites_good_existing_data_with_failure(self, test_db, mock_embeddings, enrich_config):
        """If Qwen fails for an org (returns None), existing good data in
        registry_enriched must be left untouched, not nulled out."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO registry_enriched
            (EIN, organization_name, NTEE1, mission, cause_tags, website)
            VALUES ('777666555', 'Org With Existing Data', 'B', 'Existing mission', '', '')
        """)
        test_db.commit()

        def failing_qwen(prompt: str, max_tokens: int = 200) -> str:
            raise Exception("simulated failure")

        from scripts.enrich_batch import EnrichmentBatch

        with patch('scripts.enrich_batch.validate_and_fetch_website', return_value=None):
            batch = EnrichmentBatch(
                db_con=test_db, qwen_fn=failing_qwen, embeddings_fn=mock_embeddings,
                config=enrich_config
            )
            batch.run(dry_run=False, max_orgs=1)

        cursor.execute("SELECT mission, cause_tags FROM registry_enriched WHERE EIN = ?", ('777666555',))
        mission, cause_tags = cursor.fetchone()
        assert mission == 'Existing mission'  # untouched
        assert cause_tags == ''  # untouched (empty, not corrupted)

    def test_mission_promotion_guard_does_not_overwrite_strong_existing_source(
        self, test_db, mock_qwen, mock_embeddings, enrich_config
    ):
        """Task 6 fix: _promote_to_registry's mission branch now re-checks the
        same "is this mission weak?" condition (mission empty, or
        mission_source in (None, 'ai_ntee', 'template_ntee')) at the point of
        writing, as defense-in-depth against overwriting a genuinely good
        mission with a guess - matching the never-overwrite-good-data pattern
        already used for cause_tags/website/donate_url.

        This directly constructs a 'mission' enrichment result for an org
        whose registry_enriched.mission_source is 'scraped' (a strong,
        non-weak source not in the regenerate-trigger list) and calls
        _promote_to_registry directly, bypassing the upstream _enrich_layer
        gate entirely - proving the DB-level guard itself is what blocks the
        overwrite, not just the upstream decision not to regenerate.
        """
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO registry_enriched
            (EIN, organization_name, NTEE1, mission, mission_source, cause_tags, website)
            VALUES ('555444333', 'Strong Source Org', 'B', 'A real, human-written mission.', 'scraped', '', '')
        """)
        test_db.commit()

        from scripts.enrich_batch import EnrichmentBatch
        batch = EnrichmentBatch(
            db_con=test_db, qwen_fn=mock_qwen, embeddings_fn=mock_embeddings,
            config=enrich_config
        )
        batch._promote_to_registry([{
            'org_ein': '555444333',
            'enrichment_type': 'mission',
            'generated_value': 'A generated replacement mission.',
            'confidence_score': 0.85,
            'context_used': '{"mission_source": "ai_web_grounded"}',
        }])

        cursor.execute(
            "SELECT mission, mission_source FROM registry_enriched WHERE EIN = ?",
            ('555444333',)
        )
        mission, mission_source = cursor.fetchone()
        assert mission == 'A real, human-written mission.'  # untouched
        assert mission_source == 'scraped'  # untouched

    def test_donate_url_below_threshold_flagged_for_human_review(self, test_db, mock_embeddings, enrich_config):
        """Low-confidence donate_url candidates must set donate_human_review=1
        and NOT be written as the live donate_url — existing pattern from
        donation_link_pipeline.py, must be preserved here."""
        cursor = test_db.cursor()
        cursor.execute("""
            INSERT INTO registry_enriched
            (EIN, organization_name, NTEE1, mission, cause_tags, website, donate_url, donate_human_review)
            VALUES ('666555444', 'Low Confidence Org', 'B', 'Test mission', 'Education', 'testorg.org', NULL, NULL)
        """)
        test_db.commit()

        # A donate_fn that returns a candidate with no corroborating evidence
        # at all (empty page content) -> identity_match returns 'mismatch' or
        # 'unknown' -> score_confidence stays low -> must be flagged, not written.
        def low_confidence_qwen(prompt: str, max_tokens: int = 200) -> str:
            if "donate" in prompt.lower():
                return "unrelatedcharity.org/give"
            return "Education, Community"

        from scripts.enrich_batch import EnrichmentBatch

        with patch('scripts.enrich_batch.validate_and_fetch_website', return_value=None):
            batch = EnrichmentBatch(
                db_con=test_db, qwen_fn=low_confidence_qwen, embeddings_fn=mock_embeddings,
                config=enrich_config
            )
            batch.run(dry_run=False, max_orgs=1)

        cursor.execute(
            "SELECT donate_url, donate_human_review FROM registry_enriched WHERE EIN = ?",
            ('666555444',)
        )
        donate_url, donate_human_review = cursor.fetchone()
        assert donate_url is None  # not written — below threshold
        assert donate_human_review == 1  # flagged for review
