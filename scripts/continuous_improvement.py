"""
Daanaa Continuous Improvement Engine

Analyzes engagement data from campaigns, social, email, and claims.
Generates insights and auto-suggests carousel topics, email optimizations, and partners.

Runs weekly/monthly/quarterly to feed the system with learning + optimization recommendations.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
import re


@dataclass
class WeeklyAnalysis:
    """Weekly learning output."""
    week_of: datetime
    top_themes: List[Tuple[str, int]]
    suggested_carousels: List[str]
    top_performing_carousel: Optional[Dict]
    nonprofit_claim_rate: float
    donor_engagement_rate: float
    email_metrics: Dict
    next_week_focus: str


class ContinuousImprovementEngine:
    """
    Analyzes platform engagement and suggests optimizations.

    Strategy: Learn from what works, surface recommendations to humans.
    No automation — all suggestions are reviewed + approved.
    """

    def __init__(self, db_path: str = "/home/akbar/meritgiving/data/merit_registry.db"):
        self.db_path = db_path
        self.db = None
        self.init_db()

    def init_db(self):
        """Initialize learning + insights tables."""
        self.db = sqlite3.connect(self.db_path)
        cursor = self.db.cursor()

        # Learning logs: captures insights from each analysis cycle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_logs (
                id TEXT PRIMARY KEY,
                cycle_date TIMESTAMP,
                cycle_type TEXT,  -- 'weekly', 'monthly', 'quarterly'
                insights TEXT,  -- JSON blob
                suggestions TEXT,  -- JSON blob
                actions_taken TEXT,  -- JSON blob
                results TEXT,  -- JSON blob
                created_at TIMESTAMP
            )
        """)

        # Optimization suggestions: specific, ranked recommendations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimization_suggestions (
                id TEXT PRIMARY KEY,
                optimization_type TEXT,  -- 'carousel_topic', 'email_subject', 'send_time', etc
                priority INTEGER,  -- 1-5, higher = more urgent
                description TEXT,
                expected_impact TEXT,
                suggested_action TEXT,
                data_basis TEXT,  -- What metrics support this
                created_at TIMESTAMP,
                status TEXT  -- 'new', 'tested', 'implemented', 'rejected'
            )
        """)

        self.db.commit()

    def weekly_analysis(self) -> Dict:
        """
        Analyze the past week and generate insights + recommendations.
        """
        week_ago = datetime.now() - timedelta(days=7)

        insights = {
            "themes": self._extract_themes(week_ago),
            "carousel_performance": self._analyze_carousel_performance(week_ago),
            "nonprofit_pipeline": self._analyze_nonprofit_pipeline(week_ago),
            "donor_engagement": self._analyze_donor_engagement(week_ago),
            "email_performance": self._analyze_email_performance(week_ago),
            "partner_opportunities": self._identify_partners(week_ago),
        }

        suggestions = self._generate_suggestions(insights)

        # Store learning log
        log_id = f"learning_{int(datetime.now().timestamp())}"
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO learning_logs
            (id, cycle_date, cycle_type, insights, suggestions, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            log_id, datetime.now(), "weekly",
            json.dumps(insights, default=str),
            json.dumps(suggestions, default=str),
            datetime.now()
        ))
        self.db.commit()

        return {
            "week_of": week_ago.isoformat(),
            "insights": insights,
            "suggestions": suggestions,
            "learning_id": log_id,
        }

    def _extract_themes(self, since: datetime) -> List[Dict]:
        """Extract recurring themes from comments."""
        cursor = self.db.cursor()

        # Get recent comments
        cursor.execute("""
            SELECT comment_text FROM comments
            WHERE collected_at > ?
            ORDER BY collected_at DESC
            LIMIT 200
        """, (since,))

        comments = [row[0] for row in cursor.fetchall()]

        # Keyword extraction
        keywords = {}
        theme_words = [
            "reserve", "funding", "small nonprofit", "visibility", "donor",
            "nonprofit leader", "financial data", "transparency", "mission",
            "sector data", "nonprofit discovery", "funding model", "giving",
            "nonprofit accountability", "nonprofit research", "nonprofit sector"
        ]

        for comment in comments:
            comment_lower = comment.lower()
            for word in theme_words:
                if word in comment_lower:
                    keywords[word] = keywords.get(word, 0) + 1

        # Sort by frequency
        top_themes = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:5]

        return [
            {
                "theme": theme,
                "frequency": count,
                "appears_in_pct": round(count / len(comments) * 100, 1) if comments else 0
            }
            for theme, count in top_themes if count >= 2
        ]

    def _analyze_carousel_performance(self, since: datetime) -> Dict:
        """Analyze which carousel types are working best."""
        cursor = self.db.cursor()

        cursor.execute("""
            SELECT carousel_type, title, COUNT(*) as impressions,
                   SUM(CASE WHEN metric_type = 'clicks' THEN metric_value ELSE 0 END) as clicks
            FROM campaigns c
            LEFT JOIN campaign_analytics a ON c.id = a.campaign_id
            WHERE c.posted_at > ?
            GROUP BY c.id
            ORDER BY impressions DESC
        """, (since,))

        results = cursor.fetchall()

        if not results:
            return {"status": "no_data"}

        top_carousel = results[0]
        carousel_types = {}

        for carousel_type, title, impressions, clicks in results:
            if carousel_type not in carousel_types:
                carousel_types[carousel_type] = {
                    "title": title,
                    "impressions": 0,
                    "clicks": 0,
                    "count": 0
                }
            carousel_types[carousel_type]["impressions"] += impressions or 0
            carousel_types[carousel_type]["clicks"] += clicks or 0
            carousel_types[carousel_type]["count"] += 1

        return {
            "top_carousel": {
                "title": top_carousel[1],
                "impressions": top_carousel[2],
                "clicks": top_carousel[3],
                "ctr": round(top_carousel[3] / top_carousel[2] * 100, 1) if top_carousel[2] else 0
            },
            "by_type": carousel_types,
        }

    def _analyze_nonprofit_pipeline(self, since: datetime) -> Dict:
        """Analyze nonprofit claim funnel."""
        cursor = self.db.cursor()

        # Total nonprofits discovered
        cursor.execute("""
            SELECT COUNT(*) FROM nonprofits_engaged
            WHERE first_seen_date > ?
        """, (since,))
        discovered = cursor.fetchone()[0]

        # Claims started
        cursor.execute("""
            SELECT COUNT(*) FROM nonprofits_engaged
            WHERE claim_started_date > ?
        """, (since,))
        started = cursor.fetchone()[0]

        # Claims completed
        cursor.execute("""
            SELECT COUNT(*) FROM nonprofits_engaged
            WHERE claim_completed_date > ?
        """, (since,))
        completed = cursor.fetchone()[0]

        return {
            "discovered": discovered,
            "started_claim": started,
            "completed_claim": completed,
            "claim_start_rate_pct": round(started / discovered * 100, 1) if discovered > 0 else 0,
            "completion_rate_pct": round(completed / started * 100, 1) if started > 0 else 0,
        }

    def _analyze_donor_engagement(self, since: datetime) -> Dict:
        """Analyze donor engagement patterns."""
        cursor = self.db.cursor()

        # Total donors
        cursor.execute("""
            SELECT COUNT(DISTINCT entity_id) FROM interactions
            WHERE entity_type = 'donor' AND recorded_at > ?
        """, (since,))
        total_donors = cursor.fetchone()[0]

        # By status
        cursor.execute("""
            SELECT engagement_status, COUNT(*)
            FROM donors_engaged
            WHERE last_interaction_date > ?
            GROUP BY engagement_status
        """, (since,))

        status_breakdown = {row[0]: row[1] for row in cursor.fetchall()}

        return {
            "total_unique_donors": total_donors,
            "by_status": status_breakdown,
        }

    def _analyze_email_performance(self, since: datetime) -> Dict:
        """Analyze email campaign metrics."""
        cursor = self.db.cursor()

        cursor.execute("""
            SELECT COUNT(*), COUNT(opened_at), COUNT(clicked_at)
            FROM email_sequences
            WHERE sent_at > ?
        """, (since,))

        sent, opened, clicked = cursor.fetchone()

        open_rate = (opened / sent * 100) if sent > 0 else 0
        click_rate = (clicked / sent * 100) if sent > 0 else 0

        return {
            "sent": sent or 0,
            "opened": opened or 0,
            "open_rate_pct": round(open_rate, 1),
            "clicked": clicked or 0,
            "click_rate_pct": round(click_rate, 1),
        }

    def _identify_partners(self, since: datetime) -> List[Dict]:
        """Identify high-potential partners from comments."""
        cursor = self.db.cursor()

        cursor.execute("""
            SELECT p.partner_name, p.partner_type, p.reach_estimate,
                   p.mission_alignment, p.conversation_status
            FROM partners_potential p
            WHERE p.first_engagement_date > ?
            AND p.mission_alignment > 0.7
            ORDER BY p.reach_estimate DESC
            LIMIT 5
        """, (since,))

        partners = []
        for row in cursor.fetchall():
            partners.append({
                "name": row[0],
                "type": row[1],
                "reach": row[2],
                "alignment": row[3],
                "status": row[4]
            })

        return partners

    def _generate_suggestions(self, insights: Dict) -> List[Dict]:
        """Generate optimization suggestions from insights."""
        suggestions = []

        # Carousel topic suggestions (from themes)
        if insights["themes"]:
            top_theme = insights["themes"][0]
            carousel_mapping = {
                "reserve": "Sample 1: Reserve Crisis (high performing for sector awareness)",
                "funding": "Sample 2: Fundraising Tax (high performing for nonprofit leaders)",
                "small nonprofit": "Sample 4: Find Your Cause (high performing for donors)",
                "visibility": "Sample 3: Funding Paradox (data storytelling)",
                "nonprofit leader": "Sample 2: Fundraising Tax (direct to stakeholders)",
            }

            if top_theme["theme"] in carousel_mapping:
                suggestions.append({
                    "type": "carousel_topic",
                    "priority": 1,
                    "suggestion": f"Next carousel: {carousel_mapping[top_theme['theme']]}",
                    "reason": f"'{top_theme['theme']}' mentioned in {top_theme['frequency']} comments ({top_theme['appears_in_pct']}% of sample)",
                    "expected_impact": "Higher engagement from people asking about this topic",
                })

        # Email optimization (from performance)
        if insights["email_performance"]["open_rate_pct"] < 25:
            suggestions.append({
                "type": "email_optimization",
                "priority": 2,
                "suggestion": "Test new subject lines",
                "reason": f"Open rate is {insights['email_performance']['open_rate_pct']}% (target: 25%)",
                "expected_impact": "Improved email engagement and click-through",
            })

        # Nonprofit pipeline (from claim funnel)
        nonprofit_insights = insights["nonprofit_pipeline"]
        if nonprofit_insights["claim_start_rate_pct"] < 20:
            suggestions.append({
                "type": "carousel_copy",
                "priority": 2,
                "suggestion": "Add claim button to carousel template",
                "reason": f"Only {nonprofit_insights['claim_start_rate_pct']}% of discovered nonprofits start claiming",
                "expected_impact": "Increase nonprofit claims by 30-50%",
            })

        # Partner opportunities
        if insights["partner_opportunities"]:
            best_partner = insights["partner_opportunities"][0]
            suggestions.append({
                "type": "partnership",
                "priority": 2,
                "suggestion": f"Reach out to {best_partner['name']} ({best_partner['type']})",
                "reason": f"High alignment ({best_partner['alignment']:.1f}), large reach ({best_partner['reach']:,} followers)",
                "expected_impact": "Co-marketing opportunity, audience expansion",
            })

        # Donor engagement (if low)
        if insights["donor_engagement"]["total_unique_donors"] < 100:
            suggestions.append({
                "type": "distribution",
                "priority": 1,
                "suggestion": "Increase carousel frequency or reach",
                "reason": f"Only {insights['donor_engagement']['total_unique_donors']} unique donors this week",
                "expected_impact": "More potential supporters reached, higher claims",
            })

        return suggestions

    def monthly_analysis(self) -> Dict:
        """Deeper monthly analysis of trends + patterns."""
        month_ago = datetime.now() - timedelta(days=30)

        cursor = self.db.cursor()

        # Total claims this month
        cursor.execute("""
            SELECT COUNT(*) FROM nonprofits_engaged
            WHERE claim_completed_date > ?
        """, (month_ago,))
        monthly_claims = cursor.fetchone()[0]

        # Email performance trends
        cursor.execute("""
            SELECT AVG(open_rate), AVG(click_rate)
            FROM (
                SELECT
                    COUNT(opened_at) * 100.0 / COUNT(*) as open_rate,
                    COUNT(clicked_at) * 100.0 / COUNT(*) as click_rate
                FROM email_sequences
                WHERE sent_at > ?
                GROUP BY DATE(sent_at)
            )
        """, (month_ago,))

        result = cursor.fetchone()
        avg_open_rate, avg_click_rate = result if result else (0, 0)

        return {
            "month_of": month_ago.isoformat(),
            "nonprofit_claims": monthly_claims,
            "avg_email_open_rate": round(avg_open_rate, 1) if avg_open_rate else 0,
            "avg_email_click_rate": round(avg_click_rate, 1) if avg_click_rate else 0,
        }

    def quarterly_analysis(self) -> Dict:
        """High-level quarterly business metrics."""
        quarter_ago = datetime.now() - timedelta(days=90)

        cursor = self.db.cursor()

        # Total nonprofits engaged
        cursor.execute("""
            SELECT COUNT(*) FROM nonprofits_engaged
            WHERE first_seen_date > ?
        """, (quarter_ago,))
        total_nonprofits = cursor.fetchone()[0]

        # Total claims
        cursor.execute("""
            SELECT COUNT(*) FROM nonprofits_engaged
            WHERE claim_completed_date > ?
        """, (quarter_ago,))
        total_claims = cursor.fetchone()[0]

        # Unique donors
        cursor.execute("""
            SELECT COUNT(DISTINCT donor_identifier) FROM donors_engaged
            WHERE first_seen_date > ?
        """, (quarter_ago,))
        total_donors = cursor.fetchone()[0]

        # Partners engaged
        cursor.execute("""
            SELECT COUNT(*) FROM partners_potential
            WHERE first_engagement_date > ?
        """, (quarter_ago,))
        total_partners = cursor.fetchone()[0]

        return {
            "quarter_of": quarter_ago.isoformat(),
            "nonprofits_discovered": total_nonprofits,
            "nonprofits_claimed": total_claims,
            "claim_rate_pct": round(total_claims / total_nonprofits * 100, 1) if total_nonprofits > 0 else 0,
            "unique_donors": total_donors,
            "potential_partners": total_partners,
        }

    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()


if __name__ == "__main__":
    # Test the engine
    engine = ContinuousImprovementEngine()

    # Weekly analysis
    weekly = engine.weekly_analysis()
    print("Weekly Analysis:")
    print(f"  Themes: {weekly['insights'].get('themes', [])}")
    print(f"  Suggestions: {len(weekly['suggestions'])} recommendations")
    for s in weekly['suggestions'][:2]:
        print(f"    - {s['suggestion']} (priority {s['priority']})")

    # Monthly analysis
    monthly = engine.monthly_analysis()
    print(f"\nMonthly Claims: {monthly['nonprofit_claims']}")

    # Quarterly analysis
    quarterly = engine.quarterly_analysis()
    print(f"\nQuarterly Impact:")
    print(f"  Nonprofits discovered: {quarterly['nonprofits_discovered']}")
    print(f"  Nonprofits claimed: {quarterly['nonprofits_claimed']}")
    print(f"  Claim rate: {quarterly['claim_rate_pct']}%")

    engine.close()
