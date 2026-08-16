#!/usr/bin/env python3
"""
Continuous discovery daemon.

Runs 24/7, finding and verifying links. Verified links queued for
batch deployment every 4 hours.

Process:
1. Find orgs without links
2. Discover links on their websites
3. Verify links are live + correct type
4. Queue verified links for deployment
5. Repeat continuously (rate-limited to avoid overwhelming servers)
"""

import sqlite3
import threading
import time
import json
import sys
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from scripts.discovery.website_discovery_comprehensive import WebsiteDiscovery
from scripts.verify_discovered_links import LinkVerifier
from scripts.discovery.gpu_link_verifier import GPULinkVerifier

try:
    from charity_navigator_verify import CharityNavigatorVerifier
    CN_AVAILABLE = True
except ImportError:
    CN_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler('/home/akbar/meritgiving/logs/discovery_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'
STATE_FILE = Path('/home/akbar/meritgiving/logs/discovery_daemon_state.json')


def _json_safe(obj):
    """JSON default: coerce numpy scalars to native Python types.

    Guards json.dumps against numpy float32/int64 leaking in from GPU
    verification (not JSON serializable → would crash the queue write).
    """
    if hasattr(obj, 'item'):  # numpy scalar
        return obj.item()
    return str(obj)


class ContinuousDiscoveryDaemon:
    """Runs discovery continuously, queuing verified links."""

    def __init__(self, use_cn_fallback=True):
        self.discovery = WebsiteDiscovery(timeout=15)
        self.verifier = LinkVerifier(timeout=10)
        self.gpu_verifier = GPULinkVerifier()  # GPU-accelerated semantic verification
        self.cn_verifier = CharityNavigatorVerifier(timeout=10) if CN_AVAILABLE and use_cn_fallback else None
        # Parallel discovery: per-thread verifier instances (requests.Session
        # is not thread-safe); GPU verifier is shared behind a lock.
        self._use_cn = CN_AVAILABLE and use_cn_fallback
        self._local = threading.local()
        self._gpu_lock = threading.Lock()
        self.stats = {
            'discovered': 0,
            'verified': 0,
            'queued': 0,
            'errors': 0,
            'cn_verified': 0,
            'gpu_verified': 0
        }
        # 2026-08-10: state published for the watchdog's health decision
        # (scripts/discovery_daemon_health.py), replacing log-text grepping
        # that silently broke when this process's batch-size argument drifted
        # out of sync with a hardcoded string in a separate file.
        self._prev_verified_snapshot = None
        self._iterations_since_verified_change = 0
        self._full_timeout_streak = 0
        self._started_at = datetime.now(timezone.utc).isoformat()

    def _write_state_snapshot(self, iteration, batch_size, workers, was_full_timeout):
        """Atomic write (tmp + rename) of authoritative daemon state, read by
        discovery_daemon_health.py. Never raises — a failure to write state
        must not crash discovery itself; the watchdog's fallback path covers
        a missing/stale state file."""
        verified_total = self.stats['verified']
        if self._prev_verified_snapshot is not None and verified_total == self._prev_verified_snapshot:
            self._iterations_since_verified_change += 1
        else:
            self._iterations_since_verified_change = 0
        self._prev_verified_snapshot = verified_total

        if was_full_timeout:
            self._full_timeout_streak += 1
        else:
            self._full_timeout_streak = 0

        state = {
            'pid': os.getpid(),
            'batch_size': batch_size,
            'workers': workers,
            'iteration': iteration,
            'verified_total': verified_total,
            'discovered_total': self.stats['discovered'],
            'gpu_verified_total': self.stats['gpu_verified'],
            'errors_total': self.stats['errors'],
            'iterations_since_verified_change': self._iterations_since_verified_change,
            'full_timeout_streak': self._full_timeout_streak,
            'started_at': self._started_at,
            'last_updated_at': datetime.now(timezone.utc).isoformat(),
        }
        try:
            tmp_path = STATE_FILE.with_suffix('.json.tmp')
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
            tmp_path.replace(STATE_FILE)  # atomic on POSIX
        except OSError as e:
            logger.warning(f"Could not write state snapshot (non-fatal): {e}")

    def get_orgs_needing_discovery(self, batch_size=50):
        """Get ALL active 501c3 organizations missing links, ordered by revenue (high to low).

        Excludes orgs already sitting in the undeployed queue and orgs
        attempted in the last 30 days. Without these, the top-revenue orgs
        were re-selected and re-crawled every batch until the 4-hourly
        deploy drained them — net throughput collapsed to ~200 links/day
        and the same sites were hit every ~10 minutes (politeness bug).
        """
        db = sqlite3.connect(str(DB), timeout=30)
        cursor = db.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS link_discovery_attempts (
                ein INTEGER PRIMARY KEY,
                attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                outcome TEXT
            )
        """)
        db.commit()

        cursor.execute("""
            SELECT EIN, organization_name, website, STATE
            FROM registry_enriched
            WHERE (
                donate_url IS NULL
                OR volunteer_url IS NULL
            )
            AND EIN > 0
            AND org_status = 'active'
            AND EIN NOT IN (SELECT ein FROM link_deployment_queue WHERE deployed_at IS NULL)
            AND EIN NOT IN (
                SELECT ein FROM link_discovery_attempts
                WHERE attempted_at >= datetime('now', '-30 days')
            )
            ORDER BY
                CASE WHEN website IS NOT NULL AND website != '' THEN 0 ELSE 1 END,
                total_revenue DESC NULLS LAST
            LIMIT ?
        """, (batch_size,))

        results = cursor.fetchall()
        db.close()
        return results

    def record_attempts(self, attempts):
        """Batch-record discovery attempts: [(ein, outcome), ...]."""
        if not attempts:
            return
        db = sqlite3.connect(str(DB), timeout=30)
        db.executemany("""
            INSERT INTO link_discovery_attempts (ein, outcome, attempted_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(ein) DO UPDATE SET
                outcome = excluded.outcome,
                attempted_at = CURRENT_TIMESTAMP
        """, attempts)
        db.commit()
        db.close()

    def apply_gpu_enhancement(self, links_dict):
        """Apply GPU semantic verification to boost confidence (non-blocking, fail-fast)."""
        if not links_dict:
            return links_dict

        # Build candidates for GPU verification
        candidates = []
        link_types = []

        if 'donate_url' in links_dict:
            candidates.append({
                'url': links_dict['donate_url'],
                'text': links_dict.get('donate_button_text', 'Donate'),
                'link_type': 'donate'
            })
            link_types.append('donate')

        if 'volunteer_url' in links_dict:
            candidates.append({
                'url': links_dict['volunteer_url'],
                'text': 'Volunteer',
                'link_type': 'volunteer'
            })
            link_types.append('volunteer')

        if not candidates:
            return links_dict

        # Run GPU verification (non-blocking with short timeout; serialized
        # across discovery threads — the verifier client is shared)
        try:
            with self._gpu_lock:
                verified = self.gpu_verifier.verify_batch(candidates)
            self.stats['gpu_verified'] += len(verified)

            # Enrich links with GPU semantic match scores
            # Cast to native float — numpy float32 is not JSON serializable
            for i, link_type in enumerate(link_types):
                if i < len(verified):
                    key_name = f'{link_type}_url'
                    if key_name in links_dict:
                        links_dict[f'{key_name}_semantic_match'] = round(float(verified[i].get('semantic_match', 0.0)), 4)
        except Exception as e:
            logger.debug(f"GPU enhancement failed (non-blocking): {e}")

        return links_dict

    def _thread_workers(self):
        """Per-thread WebsiteDiscovery/LinkVerifier/CN instances for parallel runs."""
        if not hasattr(self._local, 'discovery'):
            self._local.discovery = WebsiteDiscovery(timeout=15)
            self._local.verifier = LinkVerifier(timeout=10)
            self._local.cn = CharityNavigatorVerifier(timeout=10) if self._use_cn else None
        return self._local.discovery, self._local.verifier, self._local.cn

    def discover_and_verify_org(self, ein, name, website, state=None):
        """Discover and verify links for one org (website or CN fallback)."""
        discovery, verifier, cn_verifier = self._thread_workers()
        try:
            verified_links = {}

            # If no website, skip to CN fallback immediately
            if not website or website.strip() == '':
                if cn_verifier:
                    cn_result = cn_verifier.verify_link(ein, name, state)
                    if cn_result and cn_result.get('donation_url'):
                        verified_links['donate_url'] = cn_result['donation_url']
                        verified_links['donate_source'] = 'charity_navigator'
                        self.stats['cn_verified'] += 1
                        self.stats['verified'] += 1

                if verified_links:
                    verified_links = self.apply_gpu_enhancement(verified_links)
                    self.queue_verified_links(ein, verified_links)
                    self.stats['queued'] += 1
                    return {'status': 'success', 'verified': len(verified_links)}
                else:
                    return {'status': 'no_links'}

            # Discover from website
            result = discovery.discover_all(website)
            if 'error' in result:
                # Fall back to CN if website fetch fails
                if cn_verifier:
                    cn_result = cn_verifier.verify_link(ein, name, state)
                    if cn_result and cn_result.get('donation_url'):
                        verified_links['donate_url'] = cn_result['donation_url']
                        verified_links['donate_source'] = 'charity_navigator'
                        self.stats['cn_verified'] += 1
                        self.stats['verified'] += 1
                        verified_links = self.apply_gpu_enhancement(verified_links)
                        self.queue_verified_links(ein, verified_links)
                        self.stats['queued'] += 1
                        return {'status': 'success', 'verified': len(verified_links)}
                return {'status': 'error', 'reason': result['error']}

            # Verify donation link from website
            if result.get('donation_links'):
                donate_url = result['donation_links'][0]['url']
                verification = verifier.verify_donation_link(donate_url)
                if verification.get('verified'):
                    verified_links['donate_url'] = donate_url
                    verified_links['donate_button_text'] = result['donation_links'][0].get('text', '')
                    self.stats['verified'] += 1
                self.stats['discovered'] += 1

            # Verify volunteer link from website
            if result.get('volunteer_links'):
                volunteer_url = result['volunteer_links'][0]['url']
                verification = verifier.verify_volunteer_link(volunteer_url)
                if verification.get('verified'):
                    verified_links['volunteer_url'] = volunteer_url
                    self.stats['verified'] += 1
                self.stats['discovered'] += 1

            # GitHub (no verification needed, URL format is sufficient)
            if result.get('github_repos'):
                verified_links['github_repo'] = result['github_repos'][0]['url']

            # skills.sh (no verification needed)
            if result.get('skills_profiles'):
                verified_links['skills_sh_profile'] = result['skills_profiles'][0]['url']

            # Fallback to Charity Navigator if no donation link found (90% confidence gate)
            if not verified_links.get('donate_url') and cn_verifier:
                cn_result = cn_verifier.verify_link(ein, name, state)
                if cn_result and cn_result.get('donation_url'):
                    verified_links['donate_url'] = cn_result['donation_url']
                    verified_links['donate_source'] = 'charity_navigator'
                    self.stats['cn_verified'] += 1
                    self.stats['verified'] += 1

            if verified_links:
                verified_links = self.apply_gpu_enhancement(verified_links)
                self.queue_verified_links(ein, verified_links)
                self.stats['queued'] += 1
                return {'status': 'success', 'verified': len(verified_links)}
            else:
                return {'status': 'no_links'}

        except Exception as e:
            self.stats['errors'] += 1
            logger.warning(f"Error processing {ein}: {str(e)[:100]}")
            return {'status': 'error', 'reason': str(e)[:100]}

    def queue_verified_links(self, ein, links):
        """Queue verified links for approval.

        All verified links from discovery go to pending queue.
        These are already verified by the verification pipeline.
        Handles duplicate EINs by merging links (no UNIQUE constraint issues).
        """
        # timeout=30: parallel discovery threads write concurrently; busy-wait
        # instead of raising "database is locked"
        db = sqlite3.connect(str(DB), timeout=30)
        cursor = db.cursor()

        # Create queue table if it doesn't exist (no UNIQUE constraint — duplicates handled by merge)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS link_deployment_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ein INTEGER NOT NULL,
                links JSON NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deployed_at TIMESTAMP
            )
        """)

        # Check if org already queued (pending deployment)
        cursor.execute("SELECT id, links FROM link_deployment_queue WHERE ein = ? AND deployed_at IS NULL", (ein,))
        existing = cursor.fetchone()

        if existing:
            # Merge new links with existing queued links (no duplicates)
            existing_id, existing_links_json = existing
            existing_links = json.loads(existing_links_json) if existing_links_json else {}
            merged = {**existing_links, **links}  # New links override old ones for same key
            cursor.execute(
                "UPDATE link_deployment_queue SET links = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(merged, default=_json_safe), existing_id)
            )
            logger.debug(f"✓ {ein}: merged {len(links)} links (total now: {len(merged)})")
        else:
            # Insert new entry
            try:
                cursor.execute("""
                    INSERT INTO link_deployment_queue (ein, links, status)
                    VALUES (?, ?, 'pending')
                """, (ein, json.dumps(links, default=_json_safe)))
                logger.info(f"✓ {ein}: {len(links)} links queued for approval")
            except sqlite3.IntegrityError as e:
                # Fallback: if insert fails (edge case), update instead
                cursor.execute(
                    "UPDATE link_deployment_queue SET links = ? WHERE ein = ? AND deployed_at IS NULL",
                    (json.dumps(links, default=_json_safe), ein)
                )
                logger.debug(f"✓ {ein}: {len(links)} links queued (duplicate handled)")

        db.commit()
        db.close()

    def auto_regulate(self, base_sleep_org, base_sleep_batch):
        """Self-tune pacing based on live system health.

        Reads load average, available memory, and API health, then returns
        adjusted (sleep_org, sleep_batch). Backs off under pressure, speeds
        up when idle. Keeps the system safe without manual tuning.
        """
        try:
            # CPU load (normalized to core count)
            load_1min = os.getloadavg()[0]
            cpu_count = os.cpu_count() or 16
            load_ratio = load_1min / cpu_count

            # Available memory (fraction free)
            mem_available_gb = 0
            with open('/proc/meminfo') as f:
                for line in f:
                    if line.startswith('MemAvailable:'):
                        mem_available_gb = int(line.split()[1]) / (1024 * 1024)
                        break

            # Decide multiplier: >1 slows down, <1 speeds up
            multiplier = 1.0
            reason = "nominal"

            # Memory pressure (hard guardrail — back off aggressively)
            if mem_available_gb < 3:
                multiplier = 4.0
                reason = f"LOW MEM ({mem_available_gb:.1f}GB free)"
            elif mem_available_gb < 6:
                multiplier = 2.0
                reason = f"mem caution ({mem_available_gb:.1f}GB free)"
            # CPU pressure
            elif load_ratio > 0.9:
                multiplier = 3.0
                reason = f"HIGH LOAD ({load_ratio:.2f})"
            elif load_ratio > 0.6:
                multiplier = 1.5
                reason = f"load caution ({load_ratio:.2f})"
            # Idle — speed up (system has headroom)
            elif load_ratio < 0.3 and mem_available_gb > 12:
                multiplier = 0.5
                reason = f"idle, speeding up (load {load_ratio:.2f}, {mem_available_gb:.0f}GB free)"

            # API health check (if API is struggling, back off hard)
            try:
                import urllib.request
                with urllib.request.urlopen('http://localhost:5000/health', timeout=3) as resp:
                    if resp.status != 200:
                        multiplier = max(multiplier, 3.0)
                        reason = f"API unhealthy (HTTP {resp.status})"
            except Exception:
                multiplier = max(multiplier, 3.0)
                reason = "API unreachable — backing off"

            # Apply, with floors/ceilings to stay sane
            adj_org = max(0.05, min(2.0, base_sleep_org * multiplier))
            adj_batch = max(0.5, min(30.0, base_sleep_batch * multiplier))

            if abs(multiplier - 1.0) > 0.01:
                logger.info(f"⚙️  Auto-regulate: {reason} → sleep {adj_org:.2f}s/org, {adj_batch:.1f}s/batch")

            return adj_org, adj_batch
        except Exception as e:
            logger.debug(f"Auto-regulate failed (using base): {e}")
            return base_sleep_org, base_sleep_batch

    def run_continuous_loop(self, batch_size=50, sleep_between_batches=5, sleep_between_orgs=0.5, workers=8):
        """Run discovery continuously with auto-regulation.

        Orgs in a batch are processed by a thread pool (each org is a
        different domain, so per-domain politeness is unchanged — still one
        crawl per site). sleep_between_orgs now paces SUBMISSION into the
        pool, so auto-regulate keeps working as the health governor.
        """
        logger.info("=" * 60)
        logger.info("🚀 CONTINUOUS DISCOVERY DAEMON STARTED (auto-regulating)")
        logger.info(f"   Batch size: {batch_size} | Workers: {workers} | Base sleep: {sleep_between_orgs}s/org, {sleep_between_batches}s/batch")
        logger.info("   Pacing self-tunes on load, memory, and API health")
        logger.info("=" * 60)

        iteration = 0
        while True:
            iteration += 1
            try:
                # Auto-regulate pacing for this batch based on live system health
                adj_sleep_org, adj_sleep_batch = self.auto_regulate(sleep_between_orgs, sleep_between_batches)

                logger.info(f"[Iteration {iteration}] Fetching {batch_size} orgs needing discovery...")
                orgs = self.get_orgs_needing_discovery(batch_size)

                if not orgs:
                    logger.info("No more orgs needing discovery, waiting before retry...")
                    time.sleep(60)
                    continue

                # No context manager: on batch timeout we must abandon the
                # pool (shutdown(wait=False)) instead of joining hung threads
                # forever — one tarpit site stalled the whole daemon for 40+
                # minutes on 2026-07-19.
                pool = ThreadPoolExecutor(max_workers=workers)
                futures = {}
                for ein, name, website, state in orgs:
                    futures[pool.submit(self.discover_and_verify_org, ein, name, website, state)] = (ein, name)
                    # Submission stagger (auto-regulated rate limit)
                    time.sleep(adj_sleep_org)

                attempts = []
                done_eins = set()
                was_full_timeout = False
                try:
                    for fut in as_completed(futures, timeout=600):
                        ein, name = futures[fut]
                        done_eins.add(ein)
                        try:
                            result = fut.result()
                        except Exception as e:
                            self.stats['errors'] += 1
                            attempts.append((ein, 'error'))
                            logger.warning(f"❌ {name} ({ein}): worker crashed: {str(e)[:100]}")
                            continue
                        attempts.append((ein, result['status']))
                        if result['status'] == 'success':
                            logger.info(f"✅ {name} ({ein}): {result['verified']} links verified")
                        elif result['status'] == 'no_links':
                            logger.debug(f"⚪ {name} ({ein}): No links found")
                        else:
                            logger.warning(f"❌ {name} ({ein}): {result.get('reason')}")
                except TimeoutError:
                    stuck = [(e, n) for f, (e, n) in futures.items() if e not in done_eins]
                    # Full timeout = zero futures completed this batch at all,
                    # the thread-leak precursor pattern from the 2026-07-20
                    # incident. Distinct from a partial timeout (one slow
                    # site among many that finished fine).
                    was_full_timeout = (len(done_eins) == 0)
                    logger.warning(f"⏱️  Batch timeout (600s): abandoning {len(stuck)} stuck workers: "
                                   + ", ".join(n[:30] for _, n in stuck[:5]))
                    for ein, _name in stuck:
                        attempts.append((ein, 'timeout'))
                finally:
                    pool.shutdown(wait=False, cancel_futures=True)

                # One write per batch: keeps re-selection out of the next batch
                self.record_attempts(attempts)

                # Log progress with confidence breakdown
                db = sqlite3.connect(str(DB))
                cursor = db.cursor()
                cursor.execute("SELECT COUNT(*) FROM link_deployment_queue WHERE status = 'pending'")
                high_conf = cursor.fetchone()[0] or 0
                cursor.execute("SELECT COUNT(*) FROM link_deployment_queue WHERE status = 'under_review'")
                under_review = cursor.fetchone()[0] or 0
                db.close()

                logger.info(
                    f"[Iteration {iteration}] Progress: "
                    f"discovered={self.stats['discovered']}, "
                    f"verified={self.stats['verified']}, "
                    f"gpu_enhanced={self.stats['gpu_verified']}, "
                    f"queued={self.stats['queued']}, "
                    f"cn_verified={self.stats['cn_verified']}, "
                    f"errors={self.stats['errors']} | "
                    f"Queue: {high_conf} (90%+) | {under_review} (under review)"
                )

                self._write_state_snapshot(iteration, batch_size, workers, was_full_timeout)

                # Sleep between batches (auto-regulated)
                logger.info(f"Sleeping {adj_sleep_batch:.1f}s before next batch...")
                time.sleep(adj_sleep_batch)

            except KeyboardInterrupt:
                logger.info("⏹️  Daemon stopped by user")
                break
            except Exception as e:
                logger.error(f"Fatal error in loop: {e}")
                time.sleep(60)  # Wait before retry


if __name__ == '__main__':
    # Singleton guard: watchdog respawns raced manual restarts all day on
    # 2026-07-19, leaving duplicate daemons double-crawling the same sites.
    import fcntl
    _lock_fh = open('/home/akbar/meritgiving/logs/discovery_daemon.lock', 'w')
    try:
        fcntl.flock(_lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("Another discovery daemon holds the lock — exiting.", file=sys.stderr)
        sys.exit(0)

    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    sleep_between_orgs = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    sleep_between_batches = float(sys.argv[3]) if len(sys.argv) > 3 else 5
    # CN fallback retired 2026-07-17 (board decision): CN ToS prohibits automated
    # extraction; the unkeyed API path produced 1 link total. Re-enabling requires
    # written CN consent + founder approval (see governance/DECISION_QUEUE.md).
    use_cn = False

    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 8

    daemon = ContinuousDiscoveryDaemon(use_cn_fallback=use_cn)
    daemon.run_continuous_loop(
        batch_size=batch_size,
        sleep_between_orgs=sleep_between_orgs,
        sleep_between_batches=sleep_between_batches,
        workers=workers
    )
