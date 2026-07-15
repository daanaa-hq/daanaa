"""
Campaign Orchestrator
Coordinates carousel creation, approval, scheduling, and posting
Integrates: campaigns_api, carousel_renderer, analytics tracking
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from .carousel_renderer import CarouselRenderer, load_carousel_from_file
from .campaigns_api import get_db

CAROUSEL_DIR = Path(__file__).parent / 'linkedin' / 'carousels'
ARCHIVE_DIR = Path(__file__).parent / 'linkedin' / 'archive'

class CampaignOrchestrator:
    """Orchestrates the full campaign lifecycle"""

    def __init__(self):
        self.carousel_dir = CAROUSEL_DIR
        self.archive_dir = ARCHIVE_DIR
        self.db = get_db()

    def load_carousel(self, carousel_file: str) -> CarouselRenderer:
        """Load a carousel JSON file"""
        filepath = self.carousel_dir / carousel_file
        if not filepath.exists():
            raise FileNotFoundError(f"Carousel not found: {carousel_file}")
        return load_carousel_from_file(str(filepath))

    def create_campaign_from_carousel(self, carousel_file: str, notes: str = '') -> str:
        """
        Create a campaign from a carousel JSON file
        Returns: campaign_id
        """
        renderer = self.load_carousel(carousel_file)
        metadata = renderer.get_metadata()

        # Create campaign in API
        conn = self.db
        cursor = conn.cursor()

        campaign_id = f"camp_{metadata['id'].replace('.json', '')}"
        campaign_content = {
            'title': metadata['title'],
            'carousel_type': metadata['carousel_type'],
            'slides': renderer.slides,
            'hashtags': metadata['hashtags'],
            'linkedin_caption': renderer.render_linkedin_caption(),
            'html': renderer.render_full_carousel_html()
        }

        cursor.execute("""
            INSERT INTO campaigns (id, title, carousel_type, content, status, notes, submitted_by)
            VALUES (?, ?, ?, ?, 'draft', ?, 'orchestrator')
        """, (
            campaign_id,
            metadata['title'],
            metadata['carousel_type'],
            json.dumps(campaign_content),
            notes
        ))

        conn.commit()
        return campaign_id

    def batch_create_campaigns(self, carousel_files: list, batch_name: str = '') -> list:
        """Create multiple campaigns at once"""
        campaign_ids = []
        for carousel_file in carousel_files:
            try:
                campaign_id = self.create_campaign_from_carousel(
                    carousel_file,
                    notes=f"Batch: {batch_name}" if batch_name else ""
                )
                campaign_ids.append(campaign_id)
                print(f"✓ Created campaign: {campaign_id}")
            except Exception as e:
                print(f"✗ Failed to create from {carousel_file}: {e}")
        return campaign_ids

    def get_pending_approvals(self) -> list:
        """Get all campaigns awaiting approval"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT id, title, created_at FROM campaigns
            WHERE status = 'pending_approval'
            ORDER BY created_at ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_scheduled_posts(self) -> list:
        """Get all campaigns scheduled for posting"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT id, title, scheduled_for FROM campaigns
            WHERE status = 'scheduled'
            AND scheduled_for <= datetime('now')
            ORDER BY scheduled_for ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def generate_weekly_batch(self, week_start_date: str = None) -> list:
        """
        Generate a weekly batch of carousels (4-5 campaigns)
        Uses the CAROUSEL_INDEX schedule
        """
        if not week_start_date:
            week_start_date = datetime.now().date()

        # Map to current week's carousels
        # This would be customized based on CAROUSEL_INDEX schedule
        weekly_carousels = [
            'sample_1_reserve_crisis.json',
            'sample_2_fundraising_tax.json',
            'sample_2_invisible_97_donors.json',
            'sample_3_funding_paradox.json',
            'sample_4_find_your_cause_celebrity.json',
            'sample_5_find_your_cause_awareness_day.json',
        ]

        campaign_ids = self.batch_create_campaigns(
            weekly_carousels,
            batch_name=f"Weekly batch {week_start_date}"
        )

        return campaign_ids

    def export_campaign_for_posting(self, campaign_id: str) -> dict:
        """
        Prepare campaign for LinkedIn posting
        Returns: LinkedIn-ready data (caption, hashtags, etc.)
        """
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT content FROM campaigns WHERE id = ?
        """, (campaign_id,))

        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Campaign not found: {campaign_id}")

        content = json.loads(row['content'])

        return {
            'campaign_id': campaign_id,
            'title': content.get('title'),
            'linkedin_caption': content.get('linkedin_caption'),
            'hashtags': content.get('hashtags'),
            'carousel_file': f"carousel_{campaign_id}.html"
        }

    def archive_campaign(self, campaign_id: str) -> str:
        """Archive campaign HTML for record-keeping"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT content FROM campaigns WHERE id = ?
        """, (campaign_id,))

        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Campaign not found: {campaign_id}")

        content = json.loads(row['content'])
        html = content.get('html', '')

        # Save to archive
        archive_file = self.archive_dir / f"{campaign_id}.html"
        archive_file.parent.mkdir(parents=True, exist_ok=True)

        with open(archive_file, 'w') as f:
            f.write(html)

        return str(archive_file)

    def generate_weekly_report(self) -> dict:
        """Generate weekly performance report"""
        week_ago = datetime.now() - timedelta(days=7)

        cursor = self.db.cursor()

        # Get posted campaigns
        cursor.execute("""
            SELECT id, title, posted_at FROM campaigns
            WHERE status = 'posted' AND posted_at > ?
            ORDER BY posted_at DESC
        """, (week_ago,))

        posted_campaigns = [dict(row) for row in cursor.fetchall()]

        # Get analytics
        analytics_summary = {}
        for campaign in posted_campaigns:
            cursor.execute("""
                SELECT metric_type, SUM(metric_value) as total
                FROM campaign_analytics
                WHERE campaign_id = ? AND recorded_at > ?
                GROUP BY metric_type
            """, (campaign['id'], week_ago))

            analytics_summary[campaign['id']] = {
                row['metric_type']: row['total']
                for row in cursor.fetchall()
            }

        return {
            'period': f"{week_ago.date()} to {datetime.now().date()}",
            'campaigns_posted': len(posted_campaigns),
            'campaigns': posted_campaigns,
            'analytics': analytics_summary
        }

    def validate_carousel_stewardship(self, carousel_file: str) -> dict:
        """
        Validate carousel against Stewardship principles
        Returns: validation report
        """
        renderer = self.load_carousel(carousel_file)

        report = {
            'carousel': carousel_file,
            'status': 'PASS',
            'checks': [],
            'warnings': [],
            'violations': []
        }

        # Check 1: No ranking language
        caption = renderer.render_linkedin_caption()
        ranking_words = ['best', 'worst', 'top', 'bottom', 'ranked', 'superior', 'inferior']
        for word in ranking_words:
            if word in caption.lower():
                report['violations'].append(
                    f"⚠️ P1 violation: '{word}' implies ranking"
                )

        # Check 2: No shame language
        shame_words = ['broken', 'failed', 'struggling', 'drowning', 'neglected']
        for word in shame_words:
            if word in caption.lower():
                report['warnings'].append(
                    f"⚠️ P5 check: '{word}' could imply judgment"
                )

        # Check 3: No urgency/nudging
        nudge_words = ['must', 'now', 'today', 'immediately', 'act fast']
        for word in nudge_words:
            if word in caption.lower():
                report['warnings'].append(
                    f"⚠️ P1/P3 check: '{word}' may nudge donors"
                )

        # Check 4: All claims sourced
        for slide in renderer.slides:
            if slide.get('stats') and not slide.get('source'):
                report['warnings'].append(
                    f"⚠️ P3 check: Stats without source in slide '{slide.get('label')}'"
                )

        if report['violations']:
            report['status'] = 'FAIL'
        elif report['warnings']:
            report['status'] = 'PASS_WITH_NOTES'

        report['checked_at'] = datetime.now().isoformat()

        return report

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()


if __name__ == '__main__':
    # Test orchestration
    orchestrator = CampaignOrchestrator()

    print("=" * 60)
    print("CAMPAIGN ORCHESTRATOR - Test Run")
    print("=" * 60)

    # Generate weekly batch
    print("\n📋 Creating weekly batch...")
    campaign_ids = orchestrator.generate_weekly_batch()
    print(f"✓ Created {len(campaign_ids)} campaigns")

    # Get pending approvals
    print("\n⏳ Pending approvals:")
    pending = orchestrator.get_pending_approvals()
    for campaign in pending:
        print(f"  - {campaign['title']} (ID: {campaign['id']})")

    # Validate stewardship
    print("\n✅ Stewardship validation:")
    test_carousel = 'sample_1_reserve_crisis.json'
    validation = orchestrator.validate_carousel_stewardship(test_carousel)
    print(f"  Status: {validation['status']}")
    if validation['warnings']:
        for warning in validation['warnings']:
            print(f"  {warning}")

    orchestrator.close()
    print("\n✓ Test complete")
