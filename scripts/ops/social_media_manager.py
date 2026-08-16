"""
Daanaa Social Media Manager

Autonomous comment monitoring, quality scoring, and engagement management.
Feeds quality engagement data back to the campaign system for continuous improvement.

Core functions:
1. Monitor LinkedIn comments on Daanaa posts
2. Score comments for quality/intent/influence (0-100 scale)
3. Extract themes from comment threads
4. Suggest response priorities
5. Auto-create nonprofit/donor/partner records for quality engagement
"""

import sqlite3
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Tuple
import os


class IntentType(Enum):
    QUESTION = "QUESTION"           # Asking for guidance
    FEEDBACK = "FEEDBACK"           # Providing input/critique
    VALIDATION = "VALIDATION"       # Agreeing/affirming
    PRAISE = "PRAISE"               # Positive sentiment
    CRITICISM = "CRITICISM"         # Negative sentiment
    INTRODUCTION = "INTRODUCTION"   # Introducing themselves/org


class AuthorInfluence(Enum):
    NONPROFIT_LEADER = "nonprofit_leader"
    IMPACT_INVESTOR = "impact_investor"
    NONPROFIT_EMPLOYEE = "nonprofit_employee"
    RESEARCHER = "researcher"
    GENERAL_USER = "general_user"


class ResponseCategory(Enum):
    ANSWER = "ANSWER"               # Direct answer to question
    RESOURCE = "RESOURCE"           # Share relevant link/tool
    INVITE = "INVITE"               # Invite to connect/explore/claim
    THANK_YOU = "THANK_YOU"         # Acknowledge contribution
    FOLLOW_UP = "FOLLOW_UP"         # Request more info


@dataclass
class Comment:
    """A single LinkedIn comment on a Daanaa post."""
    id: str
    campaign_id: str
    author_name: str
    author_handle: str
    author_followers: int
    comment_text: str
    comment_url: str
    posted_at: datetime


@dataclass
class TractionScore:
    """Quality score for a comment."""
    comment_id: str
    quality_score: int  # 0-100
    intent_type: IntentType
    intent_confidence: float
    author_influence: AuthorInfluence
    mission_alignment: float  # 0-1
    should_respond: bool
    response_category: ResponseCategory
    scored_at: datetime


class SocialMediaManager:
    """
    Manages nonprofit-discovery-platform comment monitoring and engagement.

    Strategy:
    - Quality over vanity: We score engagement by intent + influence, not impressions
    - Nonprofit-focused: Questions from nonprofit leaders are highest priority
    - Data-driven: Every response is tracked, analyzed, and used to optimize future posts
    """

    def __init__(self, db_path: str = "/home/akbar/meritgiving/data/merit_registry.db"):
        self.db_path = db_path
        self.db = None
        self.init_db()

    def init_db(self):
        """Initialize database tables for comment monitoring."""
        self.db = sqlite3.connect(self.db_path)
        cursor = self.db.cursor()

        # Comments table: raw LinkedIn comments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                campaign_id TEXT,
                author_name TEXT,
                author_handle TEXT,
                author_followers INTEGER,
                comment_text TEXT,
                comment_url TEXT,
                posted_at TIMESTAMP,
                collected_at TIMESTAMP,
                FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
            )
        """)

        # Traction scores: quality scores for each comment
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traction_scores (
                id TEXT PRIMARY KEY,
                comment_id TEXT UNIQUE,
                quality_score INTEGER,
                intent_type TEXT,
                intent_confidence REAL,
                author_influence TEXT,
                mission_alignment REAL,
                should_respond BOOLEAN,
                response_category TEXT,
                scored_at TIMESTAMP,
                FOREIGN KEY(comment_id) REFERENCES comments(id)
            )
        """)

        # Engagement themes: patterns extracted from comments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engagement_themes (
                id TEXT PRIMARY KEY,
                week_of TIMESTAMP,
                theme TEXT,
                frequency INTEGER,
                example_comments TEXT,
                associated_carousel TEXT,
                extracted_at TIMESTAMP
            )
        """)

        # Response log: tracks which comments we responded to and impact
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS response_log (
                id TEXT PRIMARY KEY,
                comment_id TEXT,
                response_text TEXT,
                response_sent_at TIMESTAMP,
                response_url TEXT,
                follow_up_engagement INTEGER DEFAULT 0,
                nonprofit_claim_created BOOLEAN DEFAULT 0,
                nonprofit_id TEXT,
                FOREIGN KEY(comment_id) REFERENCES comments(id)
            )
        """)

        self.db.commit()

    def log_comment(self, campaign_id: str, author_name: str, author_handle: str,
                   author_followers: int, comment_text: str, comment_url: str) -> str:
        """
        Log a new comment from LinkedIn.
        Returns comment ID.
        """
        comment_id = f"comment_{campaign_id}_{author_handle}_{int(datetime.now().timestamp())}"

        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO comments (id, campaign_id, author_name, author_handle,
                                 author_followers, comment_text, comment_url,
                                 posted_at, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            comment_id, campaign_id, author_name, author_handle, author_followers,
            comment_text, comment_url, datetime.now(), datetime.now()
        ))
        self.db.commit()

        return comment_id

    def score_comment(self, comment_id: str) -> TractionScore:
        """
        Score a comment for quality, intent, and response priority.

        Scoring algorithm:
        - Base: Intent detection (question=60, validation=50, feedback=45, praise=70, criticism=30)
        - Author influence bonus: nonprofit_leader +25, investor +15, employee +10
        - Mission alignment: +20 if comment aligns with nonprofit discovery/transparency mission
        - Quality multiplier: confidence × base score

        Result: 0-100 score indicating engagement quality
        """
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT c.*, t.quality_score
            FROM comments c
            LEFT JOIN traction_scores t ON c.id = t.comment_id
            WHERE c.id = ?
        """, (comment_id,))

        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Comment {comment_id} not found")

        # Already scored
        if result[-1] is not None:
            cursor.execute("SELECT * FROM traction_scores WHERE comment_id = ?", (comment_id,))
            row = cursor.fetchone()
            return self._row_to_traction_score(row)

        # Extract comment data
        comment_text = result[5]
        author_followers = result[4]

        # Detect intent type from comment text
        intent_type, intent_confidence = self._detect_intent(comment_text)

        # Detect author influence from text signals + follower count
        author_influence = self._detect_influence(comment_text, author_followers)

        # Calculate mission alignment (does comment relate to transparency, nonprofit discovery, etc?)
        mission_alignment = self._calculate_mission_alignment(comment_text)

        # Base score by intent
        intent_scores = {
            IntentType.QUESTION: 60,
            IntentType.FEEDBACK: 45,
            IntentType.VALIDATION: 50,
            IntentType.PRAISE: 70,
            IntentType.CRITICISM: 30,
            IntentType.INTRODUCTION: 55,
        }
        base_score = intent_scores.get(intent_type, 40)

        # Author influence bonus
        influence_bonus = {
            AuthorInfluence.NONPROFIT_LEADER: 25,
            AuthorInfluence.IMPACT_INVESTOR: 15,
            AuthorInfluence.NONPROFIT_EMPLOYEE: 10,
            AuthorInfluence.RESEARCHER: 8,
            AuthorInfluence.GENERAL_USER: 0,
        }
        score = base_score + influence_bonus.get(author_influence, 0)

        # Mission alignment bonus
        score += int(mission_alignment * 20)

        # Confidence multiplier
        quality_score = int(score * intent_confidence)
        quality_score = min(100, quality_score)  # Cap at 100

        # Determine if we should respond
        should_respond = quality_score >= 50 or (intent_type in [IntentType.QUESTION, IntentType.INTRODUCTION])

        # Determine response category
        response_category = self._determine_response_category(intent_type, author_influence, comment_text)

        # Store score
        score_id = f"score_{comment_id}"
        cursor.execute("""
            INSERT INTO traction_scores
            (id, comment_id, quality_score, intent_type, intent_confidence,
             author_influence, mission_alignment, should_respond, response_category, scored_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            score_id, comment_id, quality_score, intent_type.value, intent_confidence,
            author_influence.value, mission_alignment, should_respond,
            response_category.value, datetime.now()
        ))
        self.db.commit()

        return TractionScore(
            comment_id=comment_id,
            quality_score=quality_score,
            intent_type=intent_type,
            intent_confidence=intent_confidence,
            author_influence=author_influence,
            mission_alignment=mission_alignment,
            should_respond=should_respond,
            response_category=response_category,
            scored_at=datetime.now()
        )

    def _detect_intent(self, text: str) -> Tuple[IntentType, float]:
        """Detect intent type from comment text."""
        text_lower = text.lower()

        # Question patterns
        if any(word in text_lower for word in ["how", "what", "why", "when", "where", "?", "can", "do you", "does"]):
            return IntentType.QUESTION, 0.8

        # Validation patterns
        if any(word in text_lower for word in ["agree", "exactly", "yes", "true", "well said", "+1", "this"]):
            return IntentType.VALIDATION, 0.75

        # Praise patterns
        if any(word in text_lower for word in ["great", "love", "amazing", "wonderful", "excellent", "brilliant", "awesome"]):
            return IntentType.PRAISE, 0.85

        # Criticism patterns
        if any(word in text_lower for word in ["wrong", "bad", "problem", "issue", "disagree", "concern", "failing"]):
            return IntentType.CRITICISM, 0.7

        # Feedback patterns
        if any(word in text_lower for word in ["would", "suggest", "idea", "feedback", "recommend", "consider"]):
            return IntentType.FEEDBACK, 0.75

        # Introduction patterns
        if any(word in text_lower for word in ["we're", "i'm", "we are", "introducing", "nonprofit", "organization"]):
            return IntentType.INTRODUCTION, 0.8

        return IntentType.FEEDBACK, 0.5

    def _detect_influence(self, text: str, follower_count: int) -> AuthorInfluence:
        """Detect author's influence tier from text signals and follower count."""
        text_lower = text.lower()

        # Nonprofit leader signals
        if any(word in text_lower for word in ["executive director", "founder", "ceo", "board", "nonprofit leader", "leading"]):
            return AuthorInfluence.NONPROFIT_LEADER

        # Impact investor signals
        if any(word in text_lower for word in ["investor", "fund", "foundation", "grant", "philanthropist", "giving"]):
            return AuthorInfluence.IMPACT_INVESTOR

        # Nonprofit employee signals
        if any(word in text_lower for word in ["work at", "team at", "we work", "nonprofit staff", "nonprofit team"]):
            return AuthorInfluence.NONPROFIT_EMPLOYEE

        # Researcher signals
        if any(word in text_lower for word in ["research", "study", "academic", "data", "analysis", "nonprofit research"]):
            return AuthorInfluence.RESEARCHER

        # Follower count heuristic (high follower = potential influence)
        if follower_count > 10000:
            return AuthorInfluence.IMPACT_INVESTOR

        return AuthorInfluence.GENERAL_USER

    def _calculate_mission_alignment(self, text: str) -> float:
        """Calculate how well comment aligns with Daanaa's mission (0.0 to 1.0)."""
        text_lower = text.lower()
        mission_keywords = [
            "nonprofit", "discovery", "transparency", "giving", "donor", "financial",
            "accountability", "nonprofit sector", "small organization", "mission", "impact",
            "reserve", "funding", "visibility", "nonprofit leader", "nonprofit data",
            "informed giving", "nonprofit research", "nonprofit support"
        ]

        keyword_matches = sum(1 for keyword in mission_keywords if keyword in text_lower)
        alignment = min(1.0, keyword_matches / 3.0)  # Normalize: 3+ matches = perfect alignment

        return alignment

    def _determine_response_category(self, intent_type: IntentType,
                                    author_influence: AuthorInfluence,
                                    comment_text: str) -> ResponseCategory:
        """Determine the best response category for this comment."""

        # Question = answer
        if intent_type == IntentType.QUESTION:
            return ResponseCategory.ANSWER

        # Nonprofit/investor introduction = invite
        if intent_type == IntentType.INTRODUCTION:
            if author_influence in [AuthorInfluence.NONPROFIT_LEADER, AuthorInfluence.IMPACT_INVESTOR]:
                return ResponseCategory.INVITE
            return ResponseCategory.THANK_YOU

        # Praise = thank you
        if intent_type == IntentType.PRAISE:
            return ResponseCategory.THANK_YOU

        # Criticism = answer (address the concern)
        if intent_type == IntentType.CRITICISM:
            return ResponseCategory.ANSWER

        # Feedback/validation = resource or thank you
        if intent_type == IntentType.FEEDBACK:
            # If they're asking for something, provide resource
            if "link" in comment_text.lower() or "more" in comment_text.lower():
                return ResponseCategory.RESOURCE
            return ResponseCategory.THANK_YOU

        return ResponseCategory.THANK_YOU

    def get_daily_digest(self, days_back: int = 1) -> Dict:
        """
        Get a digest of high-quality comments from the past N days.
        Ready for human review/response.
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)

        cursor = self.db.cursor()
        cursor.execute("""
            SELECT c.id, c.author_name, c.author_handle, c.comment_text,
                   c.comment_url, t.quality_score, t.intent_type,
                   t.response_category, t.should_respond
            FROM comments c
            LEFT JOIN traction_scores t ON c.id = t.comment_id
            WHERE c.collected_at > ?
            AND t.quality_score >= 50 AND t.should_respond = 1
            ORDER BY t.quality_score DESC
        """, (cutoff_date,))

        high_quality = cursor.fetchall()

        digest = {
            "period": f"Last {days_back} day(s)",
            "total_comments": len(high_quality),
            "comments_to_respond": [],
            "themes": self._extract_themes(cutoff_date),
        }

        for comment in high_quality:
            digest["comments_to_respond"].append({
                "id": comment[0],
                "author": comment[1],
                "handle": comment[2],
                "text": comment[3],
                "url": comment[4],
                "quality_score": comment[5],
                "intent": comment[6],
                "response_type": comment[7],
            })

        return digest

    def _extract_themes(self, since: datetime) -> List[Dict]:
        """Extract common themes from recent comments."""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT comment_text FROM comments
            WHERE collected_at > ?
            ORDER BY collected_at DESC
            LIMIT 100
        """, (since,))

        comments = [row[0] for row in cursor.fetchall()]

        # Simple keyword frequency analysis
        keywords = {}
        theme_words = [
            "reserve", "funding", "small", "visibility", "donor", "nonprofit",
            "financial", "data", "transparency", "mission", "sector", "nonprofit leader",
            "accountability", "nonprofit discovery", "giving", "impact"
        ]

        for comment in comments:
            comment_lower = comment.lower()
            for word in theme_words:
                if word in comment_lower:
                    keywords[word] = keywords.get(word, 0) + 1

        # Return top themes
        top_themes = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:5]

        return [
            {
                "theme": theme,
                "frequency": count,
                "suggests_carousel_topic": self._suggest_carousel_topic(theme)
            }
            for theme, count in top_themes
        ]

    def _suggest_carousel_topic(self, theme: str) -> Optional[str]:
        """Suggest a carousel topic based on common theme."""
        theme_to_carousel = {
            "reserve": "Sample 1: Reserve Crisis",
            "funding": "Sample 2: Fundraising Tax",
            "small": "Sample 4: Find Your Cause",
            "visibility": "Sample 3: Funding Paradox",
            "donor": "Sample 4: Find Your Cause",
            "nonprofit": "Sample 2: Invisible 97%",
            "financial": "Sample 3: Funding Paradox",
            "sector": "Sample 1: Reserve Crisis",
            "nonprofit leader": "Sample 2: Fundraising Tax",
        }
        return theme_to_carousel.get(theme)

    def log_response(self, comment_id: str, response_text: str, response_url: str):
        """Log that we responded to a comment."""
        response_id = f"response_{comment_id}_{int(datetime.now().timestamp())}"

        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO response_log (id, comment_id, response_text, response_sent_at, response_url)
            VALUES (?, ?, ?, ?, ?)
        """, (response_id, comment_id, response_text, datetime.now(), response_url))
        self.db.commit()

    def create_nonprofit_from_comment(self, comment_id: str, nonprofit_id: str):
        """
        Mark that a high-quality comment led to creating/tracking a nonprofit record.
        Used for impact measurement.
        """
        cursor = self.db.cursor()
        cursor.execute("""
            UPDATE response_log
            SET nonprofit_claim_created = 1, nonprofit_id = ?
            WHERE comment_id = ?
        """, (nonprofit_id, comment_id))
        self.db.commit()

    def weekly_analysis(self) -> Dict:
        """
        Generate weekly analysis of engagement quality.
        Used by continuous improvement engine.
        """
        week_ago = datetime.now() - timedelta(days=7)

        cursor = self.db.cursor()

        # Get all comments from the week
        cursor.execute("""
            SELECT COUNT(*), AVG(t.quality_score), COUNT(DISTINCT c.author_handle)
            FROM comments c
            LEFT JOIN traction_scores t ON c.id = t.comment_id
            WHERE c.collected_at > ?
        """, (week_ago,))

        total, avg_quality, unique_authors = cursor.fetchone()

        # Get response stats
        cursor.execute("""
            SELECT COUNT(*), COUNT(DISTINCT CASE WHEN nonprofit_claim_created THEN comment_id END)
            FROM response_log
            WHERE response_sent_at > ?
        """, (week_ago,))

        responses, nonprofit_claims = cursor.fetchone()

        return {
            "week_of": week_ago.isoformat(),
            "total_comments": total or 0,
            "avg_quality_score": float(avg_quality) if avg_quality else 0,
            "unique_authors": unique_authors or 0,
            "responses_sent": responses or 0,
            "nonprofit_claims_created": nonprofit_claims or 0,
            "themes": self._extract_themes(week_ago),
        }

    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()


if __name__ == "__main__":
    # Test the system
    manager = SocialMediaManager()

    # Log a test comment
    comment_id = manager.log_comment(
        campaign_id="test_campaign_1",
        author_name="Jane Nonprofit Leader",
        author_handle="janelead",
        author_followers=5000,
        comment_text="This is exactly what our nonprofit community needs. How do nonprofits claim their profiles?",
        comment_url="https://linkedin.com/feed/..."
    )

    print(f"Logged comment: {comment_id}")

    # Score it
    score = manager.score_comment(comment_id)
    print(f"Quality score: {score.quality_score}/100")
    print(f"Intent: {score.intent_type.value}")
    print(f"Should respond: {score.should_respond}")
    print(f"Response type: {score.response_category.value}")

    # Get digest
    digest = manager.get_daily_digest()
    print(f"\nDaily Digest:")
    print(f"  Total high-quality comments: {digest['total_comments']}")
    print(f"  Themes: {digest['themes']}")

    manager.close()
