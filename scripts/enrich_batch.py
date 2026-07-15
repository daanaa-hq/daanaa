#!/usr/bin/env python3
"""
Main enrichment batch orchestrator.

Wires together the four enrichment pipeline modules built in Tasks 3-6:
  - SemanticLookup   (Task 3): find similar orgs via embedding similarity
  - QwenInference    (Task 4): generate cause tags + website suggestions
  - QualityMeasurement (Task 5): measure accuracy/validity of past runs
  - PromptImprovement  (Task 6): decide whether/how to improve prompts

This is the entry point that will run nightly via cron (Task 8).

Usage:
  python3 enrich_batch.py --help
  python3 enrich_batch.py --dry-run --max-orgs 100
  python3 enrich_batch.py --workers 4 --batch-size 20
"""
import sys
import sqlite3
import json
import argparse
import logging
import time
from datetime import date
from pathlib import Path
from typing import Callable, Optional, Dict, Any

# Make the repo root importable so `from scripts.X import Y` works both when
# this module is imported as `scripts.enrich_batch` (pytest, rootdir=repo
# root via pytest.ini's `pythonpath = .`) AND when this file is executed
# directly as a standalone script (`cd scripts && python3 enrich_batch.py`,
# where sys.path[0] is scripts/ itself, not the repo root). Every other test
# module in this repo imports sibling modules via `scripts.X` (see
# tests/test_semantic_lookup.py, tests/test_qwen_inference.py), so we follow
# that convention here rather than bare `import semantic_lookup` - this
# avoids the module ending up double-imported under two different names
# (`scripts.semantic_lookup` vs bare `semantic_lookup`) when both this file
# and existing tests import the same underlying module.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.semantic_lookup import SemanticLookup
from scripts.qwen_inference import QwenInference
from scripts.quality_measurement import QualityMeasurement
from scripts.prompt_improvement import PromptImprovement
from scripts.website_content import validate_and_fetch_website, fetch_known_website
from scripts.donate_confidence import score_confidence, identity_match
from scripts.website_normalize import normalize_website
from scripts.s3_enrichment import get_s3_client

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "merit_registry.db"
CONFIG_PATH = BASE / "scripts" / "enrich_batch_config.json"


def load_config() -> Dict[str, Any]:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_mock_qwen_fn() -> Callable:
    """Placeholder Qwen function for standalone CLI demo/dry-run use only.

    Production nightly runs (Task 8) must pass a real qwen_fn that calls the
    llama-server on port 11437 - this stub exists so `python3 enrich_batch.py`
    is runnable end-to-end without a live inference server. Tests must NOT
    use this; they use the real `mock_qwen` fixture from tests/fixtures.py.
    """
    def mock_qwen(prompt: str, max_tokens: int = 200) -> str:
        if "cause_tags" in prompt or "tagged" in prompt:
            return "Education, Community Development, Mentorship"
        elif "website" in prompt or "domain" in prompt:
            return "myorg.org"
        return "test response"
    return mock_qwen


def get_embeddings_fn() -> Callable:
    """Placeholder embeddings function for standalone CLI demo/dry-run use.

    Production nightly runs (Task 8) must pass a real embeddings_fn that
    calls the mxbai-embed-large server on port 11436. Tests use the real
    `mock_embeddings` fixture from tests/fixtures.py instead.
    """
    def mock_embeddings(texts: list) -> list:
        import numpy as np
        embeddings = []
        for text in texts:
            seed = sum(ord(c) for c in text) % 10000
            np.random.seed(seed)
            emb = np.random.randn(1024).astype(float).tolist()
            embeddings.append(emb)
        return embeddings
    return mock_embeddings


def get_real_qwen_fn(port: int = 11437, timeout: int = 60) -> Callable:
    """Real Qwen inference via local llama-server HTTP API.

    Talks to the OpenAI-compatible chat completions endpoint served by
    llama-server on `port` (default 11437, the Qwen2.5-32B-Instruct
    Vulkan1 server documented in CLAUDE.md). Any connection failure,
    timeout, or non-2xx response raises - QwenInference.generate_tags/
    generate_website already wrap their qwen_fn call in a bare
    `except Exception` that logs and returns None, so this is safe to let
    bubble up rather than swallowing errors here.
    """
    import requests

    def qwen_call(prompt: str, max_tokens: int = 200, schema: Optional[dict] = None) -> str:
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
        if schema:
            # llama-server converts the schema to a GBNF grammar and enforces
            # it during sampling — the model physically cannot answer with the
            # verbose prose that got Layer 1 disabled on 2026-07-08.
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "enrichment", "strict": True, "schema": schema},
            }
        resp = requests.post(
            f"http://localhost:{port}/v1/chat/completions",
            json=payload, timeout=timeout
        )
        if resp.status_code == 400 and schema:
            # Older llama-server builds reject response_format — fall back to
            # prompt-instructed JSON; QwenInference still parses fail-closed.
            payload.pop("response_format")
            resp = requests.post(
                f"http://localhost:{port}/v1/chat/completions",
                json=payload, timeout=timeout
            )
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']

    return qwen_call


def get_real_embeddings_fn(port: int = 11436, timeout: int = 60) -> Callable:
    """Real embeddings via local llama-server HTTP API.

    Talks to the llama.cpp embedding endpoint on `port` (default 11436,
    the mxbai-embed-large Vulkan1 server documented in CLAUDE.md). The
    response is doubly nested - `data[i]['embedding']` is a
    single-element list wrapping the actual 1024-dim vector - so this
    unwraps `['embedding'][0]` to return a flat list of vectors, matching
    the shape SemanticLookup/embeddings_fn callers already expect from
    the mock embeddings function.
    """
    import requests

    def embeddings_call(texts: list) -> list:
        resp = requests.post(
            f"http://localhost:{port}/embedding",
            json={"content": texts},
            timeout=timeout
        )
        resp.raise_for_status()
        data = resp.json()
        return [item['embedding'][0] for item in data]

    return embeddings_call


class EnrichmentBatch:
    """Orchestrate enrichment batch with all four layers."""

    def __init__(
        self,
        db_con: sqlite3.Connection,
        qwen_fn: Callable,
        embeddings_fn: Callable,
        config: Dict[str, Any],
        prompt_versions_file: Optional[str] = None
    ):
        self.db = db_con
        self.qwen_fn = qwen_fn
        self.embeddings_fn = embeddings_fn
        self.config = config

        # S3 client for enrichment storage (Phase 2a)
        self.s3_client = get_s3_client()
        if not self.s3_client:
            logger.warning("S3 client unavailable - enrichment data will not be stored")

        self.semantic = SemanticLookup(db_con=db_con, embeddings_fn=embeddings_fn)
        self.quality = QualityMeasurement(db_con=db_con)
        self.improver = PromptImprovement(
            db_con=db_con, config=config, prompt_versions_file=prompt_versions_file
        )

        # Close the self-improvement feedback loop: PromptImprovement already
        # loaded whatever prompt versions exist - either an auto-improved set
        # from prompt_versions_file (if generate_improved_prompt() has ever
        # written one) or, when no such file exists yet, the static
        # config['prompts'] fallback (see PromptImprovement._load_prompt_versions).
        # Either way, self.improver.prompt_versions is the source of truth for
        # "what prompt versions exist" - QwenInference must be built from that,
        # not from the raw static config, or an overnight-improved v1.2 would
        # never actually get used by tonight's batch.
        latest_version = max(
            self.improver.prompt_versions.keys(),
            key=lambda v: float(v[1:])
        )
        qwen_config = dict(config)
        qwen_config['prompts'] = self.improver.prompt_versions
        self.qwen = QwenInference(qwen_fn=qwen_fn, config=qwen_config, prompt_version=latest_version)

    def run(
        self,
        dry_run: bool = False,
        max_orgs: Optional[int] = None,
        workers: int = 1,
        batch_size: int = 20
    ) -> Dict[str, Any]:
        logger.info("=== Enrichment Batch Started ===")
        start_time = time.time()

        # Layer 1 re-enabled 2026-07-10: outputs are now grammar-constrained
        # JSON (schema kwarg → llama-server response_format) and parsed
        # fail-closed in qwen_inference.py, fixing the verbose-output problem
        # that got this disabled on 2026-07-08. Layer 2 (contact/programs/S3
        # embeddings) stays removed — zero-yield, see DECISIONS.md 2026-07-10.
        #
        # Checkpointed 2026-07-12: previously this called _enrich_layer() for
        # the WHOLE query (default LIMIT 1,000,000 — effectively the entire
        # registry, ~1.96M orgs matched the WHERE clause) and buffered every
        # result in memory, writing to the DB only once at the very end. A
        # process killed at the 8am cutoff, or any crash, lost 100% of that
        # night's work with zero rows written — this is exactly what happened
        # 2026-07-12 20:19-20:55 (35 min running, 0 rows written). Now writes
        # + commits every `batch_size` orgs so a kill/crash loses at most one
        # chunk, not the whole run.
        logger.info("Layer 1: Semantic lookup + Qwen inference (structured output)")
        enrich_results = self._enrich_layer(
            max_orgs=max_orgs, batch_size=batch_size, dry_run=dry_run
        )

        elapsed = time.time() - start_time
        stats = {
            'run_date': str(date.today()),
            'elapsed_seconds': elapsed,
            'orgs_processed': len(enrich_results),
            'tags_generated': sum(1 for r in enrich_results if r.get('enrichment_type') == 'cause_tags'),
            'websites_generated': sum(1 for r in enrich_results if r.get('enrichment_type') == 'website'),
            'dry_run': dry_run
        }

        logger.info(f"Batch complete: {stats}")
        return stats

    def _enrich_layer(
        self,
        max_orgs: Optional[int] = None,
        batch_size: int = 20,
        dry_run: bool = False
    ) -> list:
        cursor = self.db.cursor()

        # Cap default LIMIT: unset max_orgs previously defaulted to 1,000,000,
        # which matched ~1.96M orgs (essentially the entire active registry)
        # in one uncheckpointed run. 5,000 is a realistic single-invocation
        # cap for one 8pm-8am window; the outer loop script re-invokes for
        # more nights, and this can still be raised via --max-orgs.
        # DISCOVERY MODE: Prioritize finding new websites over donation links.
        # Phase 1: orgs WITHOUT website (1.9M backlog) → generate websites via Qwen
        # Phase 2: orgs WITH website but no donate_url → extract donation links
        # Phase 3: metadata-deficient orgs (cause_tags, missions)
        phase = 1

        # Phase 1: Website discovery for website-less orgs (highest gap coverage)
        cursor.execute(
            """
            SELECT EIN, organization_name, mission, mission_source, NTEE1, city, state, donate_url,
                   website, website_status
            FROM registry_enriched
            WHERE website IS NULL OR website = ''
            ORDER BY RANDOM()  -- randomize to avoid duplicate attempts
            LIMIT ?
            """,
            (max_orgs or 5000,)
        )
        orgs = cursor.fetchall()

        if len(orgs) < (max_orgs or 5000):
            # Phase 2: Donation link extraction from known websites
            phase = 2
            remaining = (max_orgs or 5000) - len(orgs)
            cursor.execute(
                """
                SELECT EIN, organization_name, mission, mission_source, NTEE1, city, state, donate_url,
                       website, website_status
                FROM registry_enriched
                WHERE website IS NOT NULL
                  AND (donate_url IS NULL OR donate_url = '')
                ORDER BY website_status = 'valid' DESC
                LIMIT ?
                """,
                (remaining,)
            )
            orgs.extend(cursor.fetchall())

        if len(orgs) < (max_orgs or 5000):
            # Phase 3: Metadata (missions, cause_tags)
            phase = 3
            remaining = (max_orgs or 5000) - len(orgs)
            cursor.execute(
                """
                SELECT EIN, organization_name, mission, mission_source, NTEE1, city, state, donate_url,
                       website, website_status
                FROM registry_enriched
                WHERE (cause_tags IS NULL OR cause_tags = '')
                   OR (mission_source IN ('ai_ntee', 'template_ntee') OR mission_source IS NULL)
                LIMIT ?
                """,
                (remaining,)
            )
            orgs.extend(cursor.fetchall())

        results = []
        last_flushed = 0  # index into `results` up to which we've already written+committed
        for i, (ein, name, mission, mission_source, ntee, city, state, existing_donate_url,
                existing_website, existing_website_status) in enumerate(orgs, 1):
            try:
                # Log phase context for hardware monitoring
                if i == 1:
                    logger.info(f"[PHASE {phase}] Starting enrichment batch with {len(orgs)} orgs")
                org_data = {
                    'EIN': ein, 'name': name, 'mission': mission,
                    'ntee': ntee, 'city': city, 'state': state
                }

                # Phase-aware enrichment: GPU allocation by discovery goal
                similar_orgs = []
                if phase == 1:
                    # Phase 1: Website discovery. Need semantic lookup + Qwen for website generation.
                    similar_orgs = self.semantic.find_similar_orgs(org_ein=ein, count=5)
                elif phase == 2:
                    # Phase 2: Donation link extraction. Skip semantic; focus on website scanning.
                    pass
                else:
                    # Phase 3: Metadata. Do semantic lookup for mission/tag context.
                    similar_orgs = self.semantic.find_similar_orgs(org_ein=ein, count=5)

                # Website: prefer the org's EXISTING confirmed website (real
                # page content, real donate/volunteer links) over asking Qwen
                # to guess a candidate domain. Found 2026-07-12: this loop
                # previously always guessed fresh regardless of whether a
                # validated website was already on file — 22,792 orgs match
                # this query with a confirmed website, and none of them ever
                # got donate/volunteer scanning or real-content mission
                # grounding because of it. fetch_known_website() reuses
                # page_cache when fresh and skips the Qwen call entirely.
                # Falls back to the original guess-and-validate flow when no
                # confirmed website exists yet.
                website_result = None
                is_known_website = bool(existing_website) and existing_website_status in ('ok', 'live')
                if is_known_website:
                    website_result = fetch_known_website(
                        db_con=self.db, ein=ein, org_name=name, known_url=existing_website
                    )

                if website_result is None:
                    is_known_website = False
                    candidate_website = self.qwen.generate_website(org_data, similar_orgs)
                    if candidate_website:
                        website_result = validate_and_fetch_website(
                            db_con=self.db, ein=ein, org_name=name,
                            candidate_url=candidate_website
                        )

                if website_result:
                    if is_known_website:
                        logger.info(
                            f"known_website_scan: ein={ein} url={website_result['url']} "
                            f"volunteer={bool(website_result.get('volunteer_url'))} "
                            f"donate={bool(website_result.get('donate_url'))}"
                        )
                    else:
                        results.append({
                            'org_ein': ein, 'enrichment_type': 'website',
                            'generated_value': website_result['url'], 'confidence_score': 0.9,
                            'context_used': json.dumps({'identity_level': website_result['identity_level']}),
                            'prompt_version': self.qwen.prompt_version
                        })
                    if website_result.get('volunteer_url'):
                        results.append({
                            'org_ein': ein, 'enrichment_type': 'volunteer_url',
                            'generated_value': website_result['volunteer_url'], 'confidence_score': 0.9,
                            'context_used': json.dumps({'source': 'scraped' if is_known_website else 'homepage_scan'}),
                            'prompt_version': self.qwen.prompt_version
                        })

                # Mission: grounded in real website content if validated,
                # else fall back to the existing NTEE/similar-org approach —
                # but only regenerate if the current mission is weak/missing.
                # Phase 2 (donation link extraction) skips this to save GPU.
                grounding_context = website_result['content_text'] if website_result else None
                if phase != 2 and (mission_source in (None, 'ai_ntee', 'template_ntee') or not mission):
                    if grounding_context:
                        new_mission = self.qwen.generate_mission_from_website(org_data, grounding_context)
                        new_mission_source = 'ai_web_grounded'
                    else:
                        new_mission = None
                        new_mission_source = None
                    if new_mission:
                        results.append({
                            'org_ein': ein, 'enrichment_type': 'mission',
                            'generated_value': new_mission, 'confidence_score': 0.85,
                            'context_used': json.dumps({'mission_source': new_mission_source}),
                            'prompt_version': self.qwen.prompt_version
                        })
                        org_data['mission'] = new_mission  # feed forward to tags below

                # Cause tags: informed by (possibly-regenerated) mission +
                # website content when available.
                # Phase 2 (donation link extraction) skips this to save GPU.
                if phase != 2:
                    tags = self.qwen.generate_tags(org_data, similar_orgs, grounding_context=grounding_context)
                    if tags:
                        results.append({
                            'org_ein': ein, 'enrichment_type': 'cause_tags',
                            'generated_value': tags, 'confidence_score': 0.7,
                            'context_used': json.dumps({'similar_count': len(similar_orgs)}),
                            'prompt_version': self.qwen.prompt_version
                        })

                # Donate URL: only attempt if none exists yet, gated through
                # the proven score_confidence()/identity_match() logic —
                # below-threshold candidates are flagged for human review,
                # never written as the live donate_url.
                #
                # Prefer a real link scraped from the CONFIRMED homepage
                # (find_donate_link, on the same already-fetched HTML as the
                # volunteer link — zero extra network/GPU cost) over asking
                # Qwen to guess a URL string. Falls back to the guess only
                # when no donate link is visible on the homepage itself;
                # donation_link_pipeline.py's Phase 1 (nightly, threaded)
                # owns deeper discovery (subdomain candidates, processor
                # recognition) for orgs where neither method finds one.
                if not existing_donate_url:
                    scraped_donate = website_result.get('donate_url') if website_result else None
                    if scraped_donate:
                        donate_candidate = scraped_donate
                        level = website_result['identity_level']
                        factors = {
                            'found_on_official_website': True,
                            'nonprofit_name_visible': level in ('exact', 'strong'),
                        }
                    else:
                        donate_candidate = self.qwen.generate_website(
                            {**org_data, 'name': f"{name} donate"}, similar_orgs
                        )
                        page_text = website_result['content_text'] if website_result else ''
                        level, ratio = identity_match(name, page_text)
                        factors = {
                            'found_on_official_website': bool(website_result),
                            'nonprofit_name_visible': level in ('exact', 'strong'),
                        }

                    if donate_candidate:
                        confidence = score_confidence(factors)
                        context = json.dumps({
                            'identity_level': level,
                            'source': 'scraped' if scraped_donate else 'qwen_guess',
                        })
                        if confidence >= 65:
                            results.append({
                                'org_ein': ein, 'enrichment_type': 'donate_url',
                                'generated_value': donate_candidate, 'confidence_score': confidence / 100.0,
                                'context_used': context,
                                'prompt_version': self.qwen.prompt_version
                            })
                        else:
                            results.append({
                                'org_ein': ein, 'enrichment_type': 'donate_url_review',
                                'generated_value': donate_candidate, 'confidence_score': confidence / 100.0,
                                'context_used': context,
                                'prompt_version': self.qwen.prompt_version
                            })
            except Exception as e:
                # Defense in depth: qwen_inference.py guards against the known
                # NULL/empty NTEE crash, but one org's unexpected failure
                # (here or in any future per-org failure mode) must never take
                # down a 1.7M-org nightly run. Log and move to the next org.
                logger.error(f"Failed to enrich org {ein}: {e}")
            finally:
                # Checkpoint every batch_size orgs (and on the final org) so a
                # kill/crash mid-run loses at most one chunk instead of the
                # entire night's work. `finally` ensures this runs even when
                # the except branch above fired for this org.
                if not dry_run and (i % batch_size == 0 or i == len(orgs)):
                    new_results = results[last_flushed:]
                    if new_results:
                        self._write_results(new_results)
                        logger.info(
                            f"Checkpoint: flushed {len(new_results)} new rows "
                            f"after {i}/{len(orgs)} orgs"
                        )
                    last_flushed = len(results)

        return results

    def _write_results(self, results: list) -> None:
        cursor = self.db.cursor()
        for result in results:
            # INSERT OR REPLACE: re-running an org on the same day updates its row
            # instead of crashing the whole batch on UNIQUE(run_date, org_ein,
            # enrichment_type) — this exact IntegrityError killed the 2026-07-12
            # parallel batch mid-run (see logs/enrichment-parallel-batch-3.log).
            cursor.execute(
                """INSERT OR REPLACE INTO enrichment_run
                   (run_date, org_ein, enrichment_type, generated_value, confidence_score, context_used, prompt_version)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(date.today()), result['org_ein'], result['enrichment_type'],
                    result['generated_value'], result['confidence_score'], result['context_used'],
                    result.get('prompt_version', 'v1.0')
                )
            )
        self.db.commit()
        self._promote_to_registry(results)

    def _promote_to_registry(self, results: list) -> None:
        """Write passing enrichment results directly to registry_enriched.

        This closes the gap where the previous build wrote only to the
        enrichment_run staging table, which nothing else ever read from —
        nothing it produced was ever visible on daanaa.org. Each org's
        promotion is independent (one failure doesn't affect others), and
        never overwrites existing data with a lower-confidence guess:
        cause_tags/website/mission only promote when the corresponding
        registry_enriched field is currently empty/weak; donate_url only
        promotes above the confidence threshold, otherwise flags human_review.
        """
        cursor = self.db.cursor()
        for result in results:
            try:
                ein = result['org_ein']
                etype = result['enrichment_type']
                value = result['generated_value']

                if etype == 'cause_tags':
                    cursor.execute(
                        "UPDATE registry_enriched SET cause_tags = ? WHERE EIN = ? AND (cause_tags IS NULL OR cause_tags = '')",
                        (value, ein)
                    )
                elif etype == 'website':
                    cursor.execute(
                        "UPDATE registry_enriched SET website = ? WHERE EIN = ? AND (website IS NULL OR website = '')",
                        (normalize_website(value), ein)
                    )
                elif etype == 'volunteer_url':
                    cursor.execute(
                        "UPDATE registry_enriched SET volunteer_url = ? WHERE EIN = ?",
                        (normalize_website(value), ein)
                    )
                elif etype == 'mission':
                    context = json.loads(result.get('context_used') or '{}')
                    mission_source = context.get('mission_source', 'ai_web_grounded')
                    # Defense-in-depth guard, mirroring the same "is this
                    # mission weak?" condition _enrich_layer already used to
                    # decide whether to generate a replacement (mission_source
                    # in (None, 'ai_ntee', 'template_ntee') or mission empty).
                    # Recomputing it here means promotion still refuses to
                    # overwrite a genuinely good mission (e.g. one already
                    # scraped or human-provided) even if it's ever called
                    # outside that upstream gate - consistent with the
                    # cause_tags/website/donate_url guards below, which never
                    # overwrite existing non-empty values with a guess.
                    cursor.execute(
                        "UPDATE registry_enriched SET mission = ?, mission_source = ? "
                        "WHERE EIN = ? AND (mission IS NULL OR mission = '' "
                        "OR mission_source IS NULL OR mission_source IN ('ai_ntee', 'template_ntee'))",
                        (value, mission_source, ein)
                    )
                elif etype == 'donate_url':
                    cursor.execute(
                        "UPDATE registry_enriched SET donate_url = ?, donate_confidence = ?, donate_human_review = 0 WHERE EIN = ? AND (donate_url IS NULL OR donate_url = '')",
                        (normalize_website(value), result['confidence_score'], ein)
                    )
                elif etype == 'donate_url_review':
                    cursor.execute(
                        "UPDATE registry_enriched SET donate_human_review = 1, donate_confidence = ? WHERE EIN = ? AND (donate_url IS NULL OR donate_url = '')",
                        (result['confidence_score'], ein)
                    )
            except Exception as e:
                logger.error(f"Failed to promote {result.get('enrichment_type')} for org {result.get('org_ein')}: {e}")
                continue
        self.db.commit()

def main():
    parser = argparse.ArgumentParser(
        description='Nonprofit enrichment batch: generate cause tags + websites'
    )
    parser.add_argument('--dry-run', action='store_true', help='Run without writing to DB')
    parser.add_argument('--max-orgs', type=int, help='Limit orgs processed (for testing)')
    parser.add_argument('--workers', type=int, default=1, help='Parallel workers')
    parser.add_argument('--batch-size', type=int, default=20, help='Orgs per inference batch')
    parser.add_argument(
        '--mock', action='store_true',
        help='Use mock Qwen/embeddings functions instead of the real local '
             'inference servers (for testing/offline use without servers running)'
    )
    parser.add_argument(
        '--qwen-port', type=int, default=11437,
        help='Port for the real Qwen llama-server (default 11437; ignored with --mock)'
    )
    parser.add_argument(
        '--embeddings-port', type=int, default=11436,
        help='Port for the real embeddings llama-server (default 11436; ignored with --mock)'
    )

    args = parser.parse_args()

    config = load_config()
    db = sqlite3.connect(str(DB_PATH), timeout=180)

    if args.mock:
        qwen_fn = get_mock_qwen_fn()
        embeddings_fn = get_embeddings_fn()
    else:
        qwen_fn = get_real_qwen_fn(port=args.qwen_port)
        embeddings_fn = get_real_embeddings_fn(port=args.embeddings_port)

    batch = EnrichmentBatch(
        db_con=db, qwen_fn=qwen_fn, embeddings_fn=embeddings_fn, config=config
    )

    stats = batch.run(
        dry_run=args.dry_run, max_orgs=args.max_orgs,
        workers=args.workers, batch_size=args.batch_size
    )

    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    main()
