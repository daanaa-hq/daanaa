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


class EnrichmentBatch:
    """Orchestrate enrichment batch with all four layers."""

    def __init__(
        self,
        db_con: sqlite3.Connection,
        qwen_fn: Callable,
        embeddings_fn: Callable,
        config: Dict[str, Any]
    ):
        self.db = db_con
        self.qwen_fn = qwen_fn
        self.embeddings_fn = embeddings_fn
        self.config = config

        self.semantic = SemanticLookup(db_con=db_con, embeddings_fn=embeddings_fn)
        self.qwen = QwenInference(qwen_fn=qwen_fn, config=config)
        self.quality = QualityMeasurement(db_con=db_con)
        self.improver = PromptImprovement(db_con=db_con, config=config)

    def run(
        self,
        dry_run: bool = False,
        max_orgs: Optional[int] = None,
        workers: int = 1,
        batch_size: int = 20
    ) -> Dict[str, Any]:
        logger.info("=== Enrichment Batch Started ===")
        start_time = time.time()

        logger.info("Layer 1: Semantic lookup + Qwen inference")
        enrich_results = self._enrich_layer(max_orgs=max_orgs, batch_size=batch_size)
        # Quality measurement + prompt improvement run separately via cron
        # (measure_quality_cron.py, improve_prompts_cron.py) - not called inline here.

        if not dry_run:
            logger.info("Writing enrichment results to DB")
            self._write_results(enrich_results)

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
        batch_size: int = 20
    ) -> list:
        cursor = self.db.cursor()

        query = """
            SELECT EIN, organization_name, mission, NTEE1, city, state
            FROM registry_enriched
            WHERE (cause_tags IS NULL OR cause_tags = '')
               OR (website IS NULL OR website = '')
            LIMIT ?
        """
        cursor.execute(query, (max_orgs or 1000000,))
        orgs = cursor.fetchall()

        results = []
        for ein, name, mission, ntee, city, state in orgs:
            try:
                org_data = {
                    'EIN': ein, 'name': name, 'mission': mission,
                    'ntee': ntee, 'city': city, 'state': state
                }

                similar_orgs = self.semantic.find_similar_orgs(org_ein=ein, count=5)

                tags = self.qwen.generate_tags(org_data, similar_orgs)
                if tags:
                    results.append({
                        'org_ein': ein, 'enrichment_type': 'cause_tags',
                        'generated_value': tags, 'confidence_score': 0.7,
                        'context_used': json.dumps({'similar_count': len(similar_orgs)})
                    })

                website = self.qwen.generate_website(org_data, similar_orgs)
                if website:
                    results.append({
                        'org_ein': ein, 'enrichment_type': 'website',
                        'generated_value': website, 'confidence_score': 0.7,
                        'context_used': json.dumps({'similar_count': len(similar_orgs)})
                    })
            except Exception as e:
                # Defense in depth: qwen_inference.py guards against the known
                # NULL/empty NTEE crash, but one org's unexpected failure
                # (here or in any future per-org failure mode) must never take
                # down a 1.7M-org nightly run. Log and move to the next org.
                logger.error(f"Failed to enrich org {ein}: {e}")
                continue

        return results

    def _write_results(self, results: list) -> None:
        cursor = self.db.cursor()
        for result in results:
            cursor.execute(
                """INSERT INTO enrichment_run
                   (run_date, org_ein, enrichment_type, generated_value, confidence_score, context_used)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    str(date.today()), result['org_ein'], result['enrichment_type'],
                    result['generated_value'], result['confidence_score'], result['context_used']
                )
            )
        self.db.commit()


def main():
    parser = argparse.ArgumentParser(
        description='Nonprofit enrichment batch: generate cause tags + websites'
    )
    parser.add_argument('--dry-run', action='store_true', help='Run without writing to DB')
    parser.add_argument('--max-orgs', type=int, help='Limit orgs processed (for testing)')
    parser.add_argument('--workers', type=int, default=1, help='Parallel workers')
    parser.add_argument('--batch-size', type=int, default=20, help='Orgs per inference batch')

    args = parser.parse_args()

    config = load_config()
    db = sqlite3.connect(str(DB_PATH), timeout=180)

    qwen_fn = get_mock_qwen_fn()
    embeddings_fn = get_embeddings_fn()
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
