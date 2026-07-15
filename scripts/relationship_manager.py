"""
Daanaa Relationship Management System (CRM)

Tracks nonprofit orgs, donors, and partners across all engagement touchpoints.
Auto-creates records from campaign engagement, claims, and social media interactions.

Core strategy:
- Every meaningful engagement creates a trackable relationship
- Relationships track interaction history, status, and next actions
- Data flows bi-directionally: claims feed relationships, relationships seed campaigns
"""

import sqlite3
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict
from enum import Enum


class NonprofitStatus(Enum):
    """Nonprofit engagement status."""
    INTERESTED = "interested"              # Discovered Daanaa
    CLAIM_STARTED = "claim_started"        # Began claiming profile
    CLAIMED = "claimed"                    # Claimed profile (complete)
    PEER_SUPPORTER = "peer_supporter"      # Active nonprofit leader using platform


class DonorStatus(Enum):
    """Donor engagement status."""
    BROWSER = "browser"                    # Browsed directory
    SEARCHER = "searcher"                  # Used search/filters
    BOOKMARKER = "bookmarker"              # Saved organizations
    DONOR_INTENT = "donor_intent"          # Gave/gave intent


class PartnerStatus(Enum):
    """Partner relationship status."""
    COLD = "cold"                          # No contact yet
    WARM = "warm"                          # Mentioned Daanaa, showed interest
    ENGAGED = "engaged"                    # Active discussion
    PARTNERING = "partnering"              # Formal partnership


class InteractionType(Enum):
    """Types of tracked interactions."""
    CAROUSEL_VIEW = "carousel_view"        # Saw carousel
    CAROUSEL_CLICK = "carousel_click"      # Clicked CTA
    SEARCH = "search"                      # Used search
    BOOKMARK = "bookmark"                  # Saved organization
    CLAIM_START = "claim_start"            # Began claim
    CLAIM_COMPLETE = "claim_complete"      # Finished claim
    COMMENT = "comment"                    # Left comment
    GIVE = "give"                          # Recorded intent to give
    EMAIL_OPEN = "email_open"              # Opened email
    EMAIL_CLICK = "email_click"            # Clicked email link


@dataclass
class NonprofitEngagement:
    """A nonprofit organization we're tracking."""
    id: str
    nonprofit_id: str
    first_seen_date: datetime
    first_carousel_source: str
    engagement_status: NonprofitStatus
    claim_started_date: Optional[datetime]
    claim_completed_date: Optional[datetime]
    profile_completeness: int  # 0-100
    interaction_count: int
    last_interaction_date: datetime
    contact_person: Optional[str]
    contact_email: Optional[str]
    notes: str
    follow_up_needed: bool
    follow_up_date: Optional[datetime]


class RelationshipManager:
    """
    Manages relationships with nonprofits, donors, and partners.

    Key principle: Every engagement creates a data point for learning + optimization.
    """

    def __init__(self, db_path: str = "/home/akbar/meritgiving/data/merit_registry.db"):
        self.db_path = db_path
        self.db = None
        self.init_db()

    def init_db(self):
        """Initialize relationship tracking tables."""
        self.db = sqlite3.connect(self.db_path)
        cursor = self.db.cursor()

        # Nonprofit engagement tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nonprofits_engaged (
                id TEXT PRIMARY KEY,
                nonprofit_id TEXT,
                first_seen_date TIMESTAMP,
                first_carousel_source TEXT,
                engagement_status TEXT,
                claim_started_date TIMESTAMP,
                claim_completed_date TIMESTAMP,
                profile_completeness INTEGER,
                interaction_count INTEGER DEFAULT 0,
                last_interaction_date TIMESTAMP,
                contact_person TEXT,
                contact_email TEXT,
                notes TEXT,
                follow_up_needed BOOLEAN DEFAULT 0,
                follow_up_date TIMESTAMP
            )
        """)

        # Donor engagement tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS donors_engaged (
                id TEXT PRIMARY KEY,
                donor_identifier TEXT,
                first_seen_date TIMESTAMP,
                first_carousel_source TEXT,
                engagement_status TEXT,
                search_queries TEXT,  -- JSON array
                bookmarked_orgs TEXT,  -- JSON array
                wallet_exists BOOLEAN,
                email_opted_in BOOLEAN,
                last_interaction_date TIMESTAMP,
                estimated_giving_intent INTEGER,
                notes TEXT
            )
        """)

        # Partner relationship tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS partners_potential (
                id TEXT PRIMARY KEY,
                partner_name TEXT,
                partner_type TEXT,
                contact_person TEXT,
                contact_email TEXT,
                reach_estimate INTEGER,
                mission_alignment REAL,
                first_engagement_date TIMESTAMP,
                engagement_signals TEXT,  -- JSON array
                conversation_status TEXT,
                conversation_notes TEXT,
                co_marketing_ideas TEXT,
                next_action TEXT,
                next_action_date TIMESTAMP
            )
        """)

        # Universal interaction log: all touchpoints across all relationship types
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id TEXT PRIMARY KEY,
                entity_id TEXT,
                entity_type TEXT,  -- 'nonprofit', 'donor', 'partner'
                interaction_type TEXT,
                interaction_data TEXT,  -- JSON blob
                recorded_at TIMESTAMP
            )
        """)

        self.db.commit()

    def track_nonprofit_from_carousel(self, nonprofit_id: str, carousel_id: str, carousel_title: str) -> str:
        """
        Create/update nonprofit engagement record from carousel click.
        """
        engagement_id = f"nonprofit_{nonprofit_id}"

        cursor = self.db.cursor()

        # Check if already tracked
        cursor.execute("SELECT id FROM nonprofits_engaged WHERE nonprofit_id = ?", (nonprofit_id,))
        existing = cursor.fetchone()

        if existing:
            # Update interaction count
            cursor.execute("""
                UPDATE nonprofits_engaged
                SET interaction_count = interaction_count + 1,
                    last_interaction_date = ?
                WHERE nonprofit_id = ?
            """, (datetime.now(), nonprofit_id))
        else:
            # Create new record
            cursor.execute("""
                INSERT INTO nonprofits_engaged
                (id, nonprofit_id, first_seen_date, first_carousel_source,
                 engagement_status, interaction_count, last_interaction_date)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (engagement_id, nonprofit_id, datetime.now(), carousel_title,
                  NonprofitStatus.INTERESTED.value, datetime.now()))

        # Log interaction
        interaction_id = f"interaction_{nonprofit_id}_{int(datetime.now().timestamp())}"
        cursor.execute("""
            INSERT INTO interactions
            (id, entity_id, entity_type, interaction_type, interaction_data, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            interaction_id, nonprofit_id, "nonprofit",
            InteractionType.CAROUSEL_CLICK.value,
            json.dumps({"carousel_id": carousel_id, "carousel_title": carousel_title}),
            datetime.now()
        ))

        self.db.commit()
        return engagement_id

    def track_nonprofit_claim_start(self, nonprofit_id: str) -> str:
        """Track when a nonprofit starts claiming their profile."""
        engagement_id = f"nonprofit_{nonprofit_id}"

        cursor = self.db.cursor()

        # Ensure record exists
        cursor.execute("SELECT id FROM nonprofits_engaged WHERE nonprofit_id = ?", (nonprofit_id,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO nonprofits_engaged
                (id, nonprofit_id, first_seen_date, engagement_status, interaction_count, last_interaction_date)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (engagement_id, nonprofit_id, datetime.now(),
                  NonprofitStatus.CLAIM_STARTED.value, datetime.now()))

        # Update to claim_started
        cursor.execute("""
            UPDATE nonprofits_engaged
            SET engagement_status = ?,
                claim_started_date = ?,
                interaction_count = interaction_count + 1,
                last_interaction_date = ?
            WHERE nonprofit_id = ?
        """, (NonprofitStatus.CLAIM_STARTED.value, datetime.now(), datetime.now(), nonprofit_id))

        # Log interaction
        interaction_id = f"interaction_{nonprofit_id}_claim_start_{int(datetime.now().timestamp())}"
        cursor.execute("""
            INSERT INTO interactions
            (id, entity_id, entity_type, interaction_type, recorded_at)
            VALUES (?, ?, ?, ?, ?)
        """, (interaction_id, nonprofit_id, "nonprofit", InteractionType.CLAIM_START.value, datetime.now()))

        self.db.commit()
        return engagement_id

    def track_nonprofit_claim_complete(self, nonprofit_id: str, completeness: int, contact_email: Optional[str] = None):
        """Track when a nonprofit completes their profile claim."""
        cursor = self.db.cursor()

        cursor.execute("""
            UPDATE nonprofits_engaged
            SET engagement_status = ?,
                claim_completed_date = ?,
                profile_completeness = ?,
                contact_email = ?,
                interaction_count = interaction_count + 1,
                last_interaction_date = ?
            WHERE nonprofit_id = ?
        """, (
            NonprofitStatus.CLAIMED.value, datetime.now(), completeness,
            contact_email, datetime.now(), nonprofit_id
        ))

        # Log interaction
        interaction_id = f"interaction_{nonprofit_id}_claim_complete_{int(datetime.now().timestamp())}"
        cursor.execute("""
            INSERT INTO interactions
            (id, entity_id, entity_type, interaction_type, interaction_data, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            interaction_id, nonprofit_id, "nonprofit", InteractionType.CLAIM_COMPLETE.value,
            json.dumps({"completeness": completeness}), datetime.now()
        ))

        self.db.commit()

    def track_donor_from_carousel(self, donor_id: str, carousel_id: str) -> str:
        """Track donor who saw carousel."""
        donor_record_id = f"donor_{donor_id}"

        cursor = self.db.cursor()

        # Check if already tracked
        cursor.execute("SELECT id FROM donors_engaged WHERE donor_identifier = ?", (donor_id,))
        existing = cursor.fetchone()

        if not existing:
            cursor.execute("""
                INSERT INTO donors_engaged
                (id, donor_identifier, first_seen_date, first_carousel_source,
                 engagement_status, last_interaction_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                donor_record_id, donor_id, datetime.now(), carousel_id,
                DonorStatus.BROWSER.value, datetime.now()
            ))

        # Log interaction
        interaction_id = f"interaction_donor_{donor_id}_{int(datetime.now().timestamp())}"
        cursor.execute("""
            INSERT INTO interactions
            (id, entity_id, entity_type, interaction_type, interaction_data, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            interaction_id, donor_id, "donor",
            InteractionType.CAROUSEL_VIEW.value,
            json.dumps({"carousel_id": carousel_id}),
            datetime.now()
        ))

        self.db.commit()
        return donor_record_id

    def track_donor_search(self, donor_id: str, search_query: str):
        """Track donor search activity."""
        cursor = self.db.cursor()

        cursor.execute("""
            UPDATE donors_engaged
            SET engagement_status = ?,
                last_interaction_date = ?
            WHERE donor_identifier = ? AND engagement_status = ?
        """, (
            DonorStatus.SEARCHER.value, datetime.now(), donor_id,
            DonorStatus.BROWSER.value
        ))

        # Log interaction
        interaction_id = f"interaction_donor_{donor_id}_search_{int(datetime.now().timestamp())}"
        cursor.execute("""
            INSERT INTO interactions
            (id, entity_id, entity_type, interaction_type, interaction_data, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            interaction_id, donor_id, "donor",
            InteractionType.SEARCH.value,
            json.dumps({"query": search_query}),
            datetime.now()
        ))

        self.db.commit()

    def track_donor_bookmark(self, donor_id: str, nonprofit_id: str):
        """Track donor bookmarking an organization."""
        cursor = self.db.cursor()

        # Update status if needed
        cursor.execute("""
            UPDATE donors_engaged
            SET engagement_status = ?,
                last_interaction_date = ?
            WHERE donor_identifier = ? AND engagement_status IN (?, ?)
        """, (
            DonorStatus.BOOKMARKER.value, datetime.now(), donor_id,
            DonorStatus.BROWSER.value, DonorStatus.SEARCHER.value
        ))

        # Log interaction
        interaction_id = f"interaction_donor_{donor_id}_bookmark_{int(datetime.now().timestamp())}"
        cursor.execute("""
            INSERT INTO interactions
            (id, entity_id, entity_type, interaction_type, interaction_data, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            interaction_id, donor_id, "donor",
            InteractionType.BOOKMARK.value,
            json.dumps({"nonprofit_id": nonprofit_id}),
            datetime.now()
        ))

        self.db.commit()

    def track_partner_from_comment(self, partner_name: str, partner_type: str,
                                   contact_handle: str, author_followers: int) -> str:
        """Auto-create partner record from high-quality LinkedIn comment."""
        partner_id = f"partner_{contact_handle}_{int(datetime.now().timestamp())}"

        cursor = self.db.cursor()

        # Estimate influence from follower count
        reach = author_followers

        cursor.execute("""
            INSERT INTO partners_potential
            (id, partner_name, partner_type, contact_person, reach_estimate,
             first_engagement_date, conversation_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            partner_id, partner_name, partner_type, contact_handle, reach,
            datetime.now(), PartnerStatus.WARM.value
        ))

        # Log interaction
        interaction_id = f"interaction_partner_{partner_id}_{int(datetime.now().timestamp())}"
        cursor.execute("""
            INSERT INTO interactions
            (id, entity_id, entity_type, interaction_type, interaction_data, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            interaction_id, partner_id, "partner",
            InteractionType.COMMENT.value,
            json.dumps({"contact_handle": contact_handle, "followers": reach}),
            datetime.now()
        ))

        self.db.commit()
        return partner_id

    def get_relationship_status(self, entity_type: str, entity_id: str) -> Dict:
        """Get current relationship status and interaction history."""
        cursor = self.db.cursor()

        if entity_type == "nonprofit":
            cursor.execute("""
                SELECT * FROM nonprofits_engaged WHERE nonprofit_id = ?
            """, (entity_id,))
            row = cursor.fetchone()
            if not row:
                return {}

            # Get interaction history
            cursor.execute("""
                SELECT interaction_type, recorded_at, interaction_data
                FROM interactions
                WHERE entity_id = ? AND entity_type = 'nonprofit'
                ORDER BY recorded_at DESC
                LIMIT 10
            """, (entity_id,))
            interactions = cursor.fetchall()

            return {
                "id": row[0],
                "nonprofit_id": row[1],
                "status": row[4],
                "claim_started": row[5],
                "claim_completed": row[6],
                "profile_completeness": row[7],
                "interaction_count": row[8],
                "last_interaction": row[9],
                "contact_email": row[11],
                "follow_up_needed": row[13],
                "interaction_history": [
                    {
                        "type": i[0],
                        "date": i[1],
                        "data": json.loads(i[2]) if i[2] else {}
                    } for i in interactions
                ]
            }

        elif entity_type == "donor":
            cursor.execute("""
                SELECT * FROM donors_engaged WHERE donor_identifier = ?
            """, (entity_id,))
            row = cursor.fetchone()
            if not row:
                return {}

            return {
                "id": row[0],
                "donor_identifier": row[1],
                "status": row[4],
                "email_opted_in": row[8],
                "interaction_count": sum(1 for _ in cursor.execute(
                    "SELECT COUNT(*) FROM interactions WHERE entity_id = ?", (entity_id,)
                ))
            }

        elif entity_type == "partner":
            cursor.execute("""
                SELECT * FROM partners_potential WHERE id = ?
            """, (entity_id,))
            row = cursor.fetchone()
            if not row:
                return {}

            return {
                "id": row[0],
                "partner_name": row[1],
                "partner_type": row[2],
                "contact_person": row[3],
                "reach_estimate": row[5],
                "mission_alignment": row[6],
                "conversation_status": row[9],
            }

        return {}

    def weekly_relationship_summary(self) -> Dict:
        """
        Generate summary of relationship activity for the week.
        Used for reporting and continuous improvement.
        """
        week_ago = datetime.now() - timedelta(days=7)

        cursor = self.db.cursor()

        # New nonprofits engaged
        cursor.execute("""
            SELECT COUNT(*) FROM nonprofits_engaged
            WHERE first_seen_date > ?
        """, (week_ago,))
        new_nonprofits = cursor.fetchone()[0]

        # Nonprofits claiming
        cursor.execute("""
            SELECT COUNT(*) FROM nonprofits_engaged
            WHERE claim_started_date > ?
        """, (week_ago,))
        claims_started = cursor.fetchone()[0]

        # Nonprofits completed
        cursor.execute("""
            SELECT COUNT(*) FROM nonprofits_engaged
            WHERE claim_completed_date > ?
        """, (week_ago,))
        claims_completed = cursor.fetchone()[0]

        # Donors engaged
        cursor.execute("""
            SELECT COUNT(DISTINCT entity_id) FROM interactions
            WHERE entity_type = 'donor' AND recorded_at > ?
        """, (week_ago,))
        donors_active = cursor.fetchone()[0]

        # Partners identified
        cursor.execute("""
            SELECT COUNT(*) FROM partners_potential
            WHERE first_engagement_date > ?
        """, (week_ago,))
        partners_new = cursor.fetchone()[0]

        return {
            "period": "last_7_days",
            "new_nonprofit_engagements": new_nonprofits,
            "nonprofit_claims_started": claims_started,
            "nonprofit_claims_completed": claims_completed,
            "active_donors": donors_active,
            "new_potential_partners": partners_new,
        }

    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()


if __name__ == "__main__":
    # Test the CRM
    rm = RelationshipManager()

    # Track a nonprofit from carousel
    nonprofit_id = "nonprofit_12345"
    nonprofit_eng_id = rm.track_nonprofit_from_carousel(
        nonprofit_id,
        "carousel_reserve_crisis",
        "Sample 1: Reserve Crisis"
    )
    print(f"Created nonprofit engagement: {nonprofit_eng_id}")

    # Track claim start
    rm.track_nonprofit_claim_start(nonprofit_id)
    print(f"Tracked claim start")

    # Check status
    status = rm.get_relationship_status("nonprofit", nonprofit_id)
    print(f"\nNonprofit status: {status['status']}")
    print(f"Interaction count: {status['interaction_count']}")

    # Track a partner from comment
    partner_id = rm.track_partner_from_comment(
        "Tech for Good Foundation",
        "foundation",
        "sarah_techforgood",
        8500
    )
    print(f"\nCreated partner: {partner_id}")

    # Weekly summary
    summary = rm.weekly_relationship_summary()
    print(f"\nWeekly summary: {summary}")

    rm.close()
