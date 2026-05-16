#!/usr/bin/env python3
"""
MERIT Data Pipeline Orchestrator
Phase 0 — Master Execution Controller

This script orchestrates all 4 workstreams in the correct order:
  1. Workstream C (IRS BMF) — Reference data first
  2. Workstream A (ProPublica) — Historical 990s
  3. Workstream B (IRS S3) — XML filings
  4. Workstream D (Master Merge) — Clean, dedup, merge

Usage:
    # Full pipeline (all workstreams)
    python orchestrator.py --all
    
    # Individual workstreams
    python orchestrator.py --workstream c
    python orchestrator.py --workstream a
    python orchestrator.py --workstream b
    python orchestrator.py --workstream d
    
    # Resume from checkpoint
    python orchestrator.py --all --resume
    
    # Dry run (show what would execute)
    python orchestrator.py --all --dry-run
"""

import argparse
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# ─── CONFIGURATION ──────────────────────────────────────────────────────────
LOG_DIR = Path("/mnt/agents/output/meritgiving/data/logs")
SCRIPTS_DIR = Path("/mnt/agents/output/meritgiving/data/scripts")

LOG_DIR.mkdir(parents=True, exist_ok=True)

# Workstream definitions with dependencies
WORKSTREAMS = {
    "c": {
        "name": "Workstream C: IRS BMF & Publication 78",
        "script": "workstream_c_irs_bmf.py",
        "args": ["--download", "--parse"],
        "depends_on": [],
        "description": "Downloads and parses IRS BMF, Publication 78, and Auto-Revocation list"
    },
    "a": {
        "name": "Workstream A: ProPublica Bulk Ingestion",
        "script": "workstream_a_propublica.py",
        "args": [],
        "depends_on": [],
        "description": "Collects 501(c)(3) orgs and financials from ProPublica API"
    },
    "b": {
        "name": "Workstream B: IRS AWS S3 XML Parsing",
        "script": "workstream_b_irs_s3.py",
        "args": ["--years", "2019,2020,2021,2022,2023"],
        "depends_on": [],
        "description": "Downloads and parses Form 990 XML from IRS S3 bucket"
    },
    "d": {
        "name": "Workstream D: Master Merge & Quality Control",
        "script": "workstream_d_master_merge.py",
        "args": ["--validate", "--output"],
        "depends_on": ["a", "b", "c"],
        "description": "Deduplicates, cleans, and merges all data into master files"
    }
}

# ─── LOGGING ────────────────────────────────────────────────────────────────
def setup_logging():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"orchestrator_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("Orchestrator")

logger = setup_logging()

# ─── EXECUTION ENGINE ───────────────────────────────────────────────────────
class PipelineOrchestrator:
    def __init__(self, dry_run: bool = False, resume: bool = False):
        self.dry_run = dry_run
        self.resume = resume
        self.completed = set()
        self.failed = set()
        self.start_times = {}
        self.end_times = {}
    
    def check_dependencies(self, ws_id: str) -> bool:
        """Check if all dependencies are satisfied."""
        ws = WORKSTREAMS[ws_id]
        for dep in ws["depends_on"]:
            if dep in self.failed:
                logger.error(f"Cannot run {ws_id}: dependency {dep} failed")
                return False
            if dep not in self.completed:
                logger.info(f"Dependency {dep} not completed yet, will run first")
                return False
        return True
    
    def run_workstream(self, ws_id: str) -> bool:
        """Execute a single workstream."""
        ws = WORKSTREAMS[ws_id]
        script_path = SCRIPTS_DIR / ws["script"]
        
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return False
        
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"Starting: {ws['name']}")
        logger.info(f"Description: {ws['description']}")
        logger.info(f"Script: {ws['script']}")
        logger.info(f"Args: {ws['args']}")
        logger.info("=" * 70)
        
        if self.dry_run:
            logger.info("[DRY RUN] Would execute:")
            logger.info(f"  python {script_path} {' '.join(ws['args'])}")
            return True
        
        self.start_times[ws_id] = time.time()
        
        try:
            cmd = [sys.executable, str(script_path)] + ws["args"]
            
            if self.resume:
                cmd.append("--resume")
            
            logger.info(f"Executing: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=False,
                text=True,
                timeout=86400  # 24 hour timeout
            )
            
            self.end_times[ws_id] = time.time()
            elapsed = self.end_times[ws_id] - self.start_times[ws_id]
            
            if result.returncode == 0:
                logger.info(f"Completed: {ws['name']} in {elapsed:.1f}s")
                self.completed.add(ws_id)
                return True
            else:
                logger.error(f"Failed: {ws['name']} (exit code {result.returncode})")
                self.failed.add(ws_id)
                return False
        
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout: {ws['name']} exceeded 24 hours")
            self.failed.add(ws_id)
            return False
        except Exception as e:
            logger.error(f"Exception in {ws['name']}: {e}")
            self.failed.add(ws_id)
            return False
    
    def run_pipeline(self, workstream_ids: List[str]):
        """Execute the full pipeline in dependency order."""
        logger.info("")
        logger.info("#" * 70)
        logger.info("# MERIT Data Pipeline — Phase 0 Orchestration")
        logger.info(f"# Start time: {datetime.now().isoformat()}")
        logger.info(f"# Workstreams: {', '.join(workstream_ids)}")
        logger.info(f"# Dry run: {self.dry_run}")
        logger.info(f"# Resume: {self.resume}")
        logger.info("#" * 70)
        
        # Resolve dependencies
        execution_order = self._resolve_dependencies(workstream_ids)
        
        logger.info(f"Execution order: {' -> '.join(execution_order)}")
        
        # Execute
        overall_start = time.time()
        
        for ws_id in execution_order:
            success = self.run_workstream(ws_id)
            if not success and not self.dry_run:
                logger.error(f"Pipeline halted due to failure in {ws_id}")
                break
        
        overall_elapsed = time.time() - overall_start
        
        # Summary
        self._print_summary(overall_elapsed)
    
    def _resolve_dependencies(self, requested: List[str]) -> List[str]:
        """Resolve execution order including dependencies."""
        resolved = []
        to_process = list(requested)
        
        while to_process:
            ws_id = to_process.pop(0)
            
            if ws_id in resolved:
                continue
            
            ws = WORKSTREAMS.get(ws_id)
            if not ws:
                logger.warning(f"Unknown workstream: {ws_id}")
                continue
            
            # Add dependencies first
            for dep in ws["depends_on"]:
                if dep not in resolved and dep not in to_process:
                    to_process.insert(0, dep)
            
            if all(dep in resolved for dep in ws["depends_on"]):
                resolved.append(ws_id)
            else:
                to_process.append(ws_id)  # Re-queue for later
        
        return resolved
    
    def _print_summary(self, total_time: float):
        logger.info("")
        logger.info("#" * 70)
        logger.info("# Pipeline Summary")
        logger.info("#" * 70)
        
        logger.info(f"\nCompleted ({len(self.completed)}):")
        for ws_id in sorted(self.completed):
            ws = WORKSTREAMS[ws_id]
            elapsed = self.end_times.get(ws_id, 0) - self.start_times.get(ws_id, 0)
            logger.info(f"  [OK] {ws['name']} — {elapsed/60:.1f} min")
        
        if self.failed:
            logger.info(f"\nFailed ({len(self.failed)}):")
            for ws_id in sorted(self.failed):
                ws = WORKSTREAMS[ws_id]
                logger.info(f"  [FAIL] {ws['name']}")
        
        logger.info(f"\nTotal elapsed time: {total_time/3600:.2f} hours")
        logger.info(f"Total elapsed time: {total_time/60:.1f} minutes")
        logger.info("#" * 70)


# ─── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="MERIT Data Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Execution Order (with --all):
  C (BMF reference) -> A (ProPublica) + B (IRS S3) -> D (Master Merge)

Examples:
  # Run complete pipeline
  python orchestrator.py --all
  
  # Run specific workstreams
  python orchestrator.py --workstream a b
  
  # Dry run
  python orchestrator.py --all --dry-run
  
  # Resume from checkpoint
  python orchestrator.py --all --resume
        """
    )
    
    parser.add_argument("--all", action="store_true", help="Run all workstreams")
    parser.add_argument(
        "--workstream",
        nargs="+",
        choices=["a", "b", "c", "d"],
        help="Specific workstreams to run"
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would execute")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoints")
    
    args = parser.parse_args()
    
    if not args.all and not args.workstream:
        parser.print_help()
        return
    
    # Determine workstreams to run
    if args.all:
        workstream_ids = ["c", "a", "b", "d"]
    else:
        workstream_ids = args.workstream
    
    # Run orchestrator
    orchestrator = PipelineOrchestrator(
        dry_run=args.dry_run,
        resume=args.resume
    )
    orchestrator.run_pipeline(workstream_ids)


if __name__ == "__main__":
    main()
