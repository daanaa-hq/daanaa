#!/usr/bin/env python3
"""
scripts/mission_generation_pipeline.py

Mission generation pipeline orchestrator.
Runs after Phase 4 (website discovery) completes.
Uses local Qwen2.5-32B inference on port 11437 (GPU).

Strategy:
1. Upgrade template_ntee missions → ai_ntee (better quality, local inference)
2. Generate missions for null/empty mission orgs
3. Resume from checkpoint (survives interruptions)

Usage:
    python3 scripts/mission_generation_pipeline.py
    python3 scripts/mission_generation_pipeline.py --limit 1000
    python3 scripts/mission_generation_pipeline.py --workers 2
    python3 scripts/mission_generation_pipeline.py --skip-upgrade  (only fill nulls)
"""

import sqlite3
import sys
import time
import argparse
from pathlib import Path
import subprocess

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"
SCRIPT_DIR = Path.home() / "meritgiving" / "scripts"
CHECKPOINT_FILE = Path.home() / "meritgiving" / ".mission_generation_checkpoint"

def get_mission_counts():
    """Get current mission stats."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cursor = conn.cursor()

    stats = {}
    cursor.execute("SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NOT NULL")
    stats['scored_orgs'] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM registry_enriched WHERE merit_score IS NOT NULL AND (mission IS NULL OR mission = '')")
    stats['need_mission'] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM registry_enriched WHERE mission_source = 'template_ntee'")
    stats['template_missions'] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM registry_enriched WHERE mission IS NOT NULL")
    stats['total_with_mission'] = cursor.fetchone()[0]

    conn.close()
    return stats

def estimate_gpu_time(org_count, batch_size=20, tokens_per_sec=46):
    """Estimate GPU time for mission generation."""
    # Qwen2.5-32B on Vulkan: ~46 tokens/sec
    # Each org takes ~80 output tokens
    # Batch overhead: ~200 input tokens per 20-org batch
    batches = (org_count + batch_size - 1) // batch_size
    total_tokens = (org_count * 80) + (batches * 200)
    hours = (total_tokens / tokens_per_sec) / 3600
    return hours

def load_checkpoint():
    """Load the last successful checkpoint."""
    if CHECKPOINT_FILE.exists():
        lines = CHECKPOINT_FILE.read_text().strip().split('\n')
        return {
            'phase': lines[0] if lines else None,
            'timestamp': lines[1] if len(lines) > 1 else None,
        }
    return {'phase': None, 'timestamp': None}

def save_checkpoint(phase):
    """Save checkpoint for resumability."""
    CHECKPOINT_FILE.write_text(f"{phase}\n{time.time()}\n")

def run_phase(phase_name, description, org_filter, limit=None, workers=1):
    """Run a mission generation phase using the existing script."""
    stats = get_mission_counts()

    if phase_name == 'upgrade':
        target_count = stats['template_missions']
        priority = "template_ntee (lower quality)"
    else:  # fill_nulls
        target_count = stats['need_mission']
        priority = "null/empty missions"

    if target_count == 0:
        print(f"✓ {phase_name}: No orgs with {priority} to process")
        return 0

    if limit:
        target_count = min(target_count, limit)

    est_hours = estimate_gpu_time(target_count)

    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MISSION GENERATION: {phase_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{description}

Orgs to process:     {target_count:,}
Priority:            {priority}
Est. GPU time:       {est_hours:.1f} hours
Workers:             {workers}
Batch size:          20 orgs (Qwen2.5-32B @ ~46 tok/sec)

Starting at:         {time.strftime('%Y-%m-%d %H:%M:%S')}
""")

    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "generate_missions.py"),
        f"--workers={workers}",
    ]

    if phase_name == 'upgrade':
        cmd.append("--upgrade-templates")

    if limit:
        cmd.append(f"--limit={limit}")

    try:
        result = subprocess.run(cmd, timeout=None)
        if result.returncode == 0:
            save_checkpoint(f"{phase_name}_complete")
            print(f"\n✓ {phase_name} completed successfully")
            return target_count
        else:
            print(f"\n✗ {phase_name} exited with code {result.returncode}")
            return 0
    except KeyboardInterrupt:
        print(f"\n⚠ {phase_name} interrupted by user (resumable from checkpoint)")
        save_checkpoint(f"{phase_name}_paused")
        return -1
    except Exception as e:
        print(f"\n✗ {phase_name} failed: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(
        description='Mission generation pipeline orchestrator'
    )
    parser.add_argument('--limit', type=int, help='Limit orgs per phase (for testing)')
    parser.add_argument('--workers', type=int, default=1, help='Parallel workers')
    parser.add_argument('--skip-upgrade', action='store_true', help='Skip upgrade phase, only fill nulls')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    args = parser.parse_args()

    checkpoint = load_checkpoint()

    print(f"""
╔════════════════════════════════════════════════════════════╗
║         MISSION GENERATION PIPELINE ORCHESTRATOR            ║
║     (Runs after Phase 4: website discovery completes)       ║
╚════════════════════════════════════════════════════════════╝

Database:            {DB_PATH}
Checkpoint:          {CHECKPOINT_FILE}
Last checkpoint:     {checkpoint['phase'] or 'none'}
Current state:       {time.strftime('%Y-%m-%d %H:%M:%S')}
""")

    stats = get_mission_counts()
    print(f"""
CURRENT STATS:
  Scored orgs:       {stats['scored_orgs']:,}
  With missions:     {stats['total_with_mission']:,}
  Need missions:     {stats['need_mission']:,}
    - template:      {stats['template_missions']:,} (upgradeable)
    - null:          {stats['need_mission'] - stats['template_missions']:,} (fill)
""")

    phases = []

    if not args.skip_upgrade:
        phases.append({
            'name': 'upgrade',
            'description': 'Upgrade template_ntee → ai_ntee/ai_web (higher quality)',
        })

    phases.append({
        'name': 'fill_nulls',
        'description': 'Fill null/empty missions (scored orgs with no description)',
    })

    completed = 0
    skipped = 0

    for phase in phases:
        # Check if already completed
        if checkpoint['phase'] and checkpoint['phase'].startswith(phase['name']):
            if checkpoint['phase'].endswith('_complete'):
                print(f"\n✓ {phase['name']} already completed (skipping)")
                skipped += 1
                continue
            elif not args.resume:
                print(f"\n⚠ {phase['name']} was paused. Use --resume to continue")
                continue

        result = run_phase(
            phase['name'],
            phase['description'],
            org_filter=None,
            limit=args.limit,
            workers=args.workers
        )

        if result > 0:
            completed += result
        elif result == -1:
            print(f"\n⚠ Pipeline paused at {phase['name']}. Checkpoint saved.")
            print(f"   Resume with: python3 scripts/mission_generation_pipeline.py --resume")
            sys.exit(0)

    # Final stats
    final_stats = get_mission_counts()
    print(f"""
╔════════════════════════════════════════════════════════════╗
║                    PIPELINE SUMMARY                         ║
╚════════════════════════════════════════════════════════════╝

Missions generated:  {completed:,}
Phases completed:    {len([p for p in phases if not (checkpoint['phase'] and checkpoint['phase'].startswith(p['name']) and not checkpoint['phase'].endswith('_complete'))])}

Final stats:
  Scored orgs:       {final_stats['scored_orgs']:,}
  With missions:     {final_stats['total_with_mission']:,}
  Still need:        {final_stats['need_mission']:,}

Next step:
  - Monitor frontend UX to verify mission quality
  - If quality is good, expand to 50K+ orgs/month during GPU idle time
  - Queue next batch by modifying mission_generation_queue.json
""")

if __name__ == '__main__':
    main()
