#!/usr/bin/env python3
"""
Deploy queued verified links to live site.

Runs every 4 hours. Deploys all links queued since last deployment,
updates database, clears queue, logs results.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.FileHandler('/home/akbar/meritgiving/logs/deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'


def deploy_queued_links():
    """Deploy all queued links to live database."""
    db = sqlite3.connect(str(DB))
    cursor = db.cursor()

    # Get all undeployed links
    cursor.execute("""
        SELECT id, ein, links
        FROM link_deployment_queue
        WHERE deployed_at IS NULL
        ORDER BY created_at ASC
    """)

    queued = cursor.fetchall()
    deployed_count = 0
    errors = 0

    logger.info(f"Deploying {len(queued)} queued link updates...")

    for queue_id, ein, links_json in queued:
        try:
            links = json.loads(links_json)

            # Update registry_enriched with verified links
            updates = []
            values = []

            if 'donate_url' in links:
                updates.append("donate_url = ?")
                updates.append("donate_url_status = 'verified'")
                updates.append("donate_checked_at = ?")
                values.extend([links['donate_url'], datetime.now().isoformat()])

            if 'donate_button_text' in links:
                updates.append("donate_button_text = ?")
                values.append(links['donate_button_text'])

            if 'volunteer_url' in links:
                updates.append("volunteer_url = ?")
                values.append(links['volunteer_url'])

            if 'github_repo' in links:
                updates.append("github_repo = ?")
                values.append(links['github_repo'])

            if 'skills_sh_profile' in links:
                updates.append("skills_sh_profile = ?")
                values.append(links['skills_sh_profile'])

            if updates:
                updates.append("updated_at = ?")
                values.append(datetime.now().isoformat())
                values.append(ein)

                query = f"UPDATE registry_enriched SET {', '.join(updates)} WHERE EIN = ?"
                cursor.execute(query, values)

                # Mark as deployed
                cursor.execute(
                    "UPDATE link_deployment_queue SET deployed_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), queue_id)
                )

                deployed_count += 1

                if deployed_count % 100 == 0:
                    logger.info(f"Deployed {deployed_count}...")

        except Exception as e:
            logger.error(f"Error deploying queue {queue_id}: {e}")
            errors += 1

    db.commit()

    # Log results
    logger.info("=" * 60)
    logger.info(f"✅ Deployment complete")
    logger.info(f"   Deployed: {deployed_count}")
    logger.info(f"   Errors: {errors}")
    logger.info(f"   Queue cleared")
    logger.info("=" * 60)

    db.close()

    return deployed_count, errors


if __name__ == '__main__':
    deployed, errors = deploy_queued_links()
    exit(0 if errors == 0 else 1)
