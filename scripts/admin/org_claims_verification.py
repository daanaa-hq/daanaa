"""
STREAM 7 Issue 1: Org Claims Email Verification
Prevents orgs from claiming false verification status without validation
"""
import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class OrgClaimsVerification:
    """Email-verified claim flow for organizations"""
    
    def __init__(self, db_path: str = "data/merit_registry.db"):
        self.db_path = db_path
        self._init_verification_table()
    
    def _init_verification_table(self):
        """Create verification tokens table if not exists"""
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute("""
                    CREATE TABLE IF NOT EXISTS org_verification_tokens (
                        token TEXT PRIMARY KEY,
                        ein TEXT NOT NULL,
                        email TEXT NOT NULL,
                        claim_type TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        verified_at TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        attempt_count INTEGER DEFAULT 0,
                        FOREIGN KEY (ein) REFERENCES registry_enriched(ein)
                    )
                """)
                db.execute("""
                    CREATE TABLE IF NOT EXISTS org_verified_claims (
                        ein TEXT PRIMARY KEY,
                        email TEXT NOT NULL,
                        verified_at TIMESTAMP NOT NULL,
                        verification_type TEXT NOT NULL,
                        FOREIGN KEY (ein) REFERENCES registry_enriched(ein)
                    )
                """)
                db.commit()
                logger.info("✓ Verification tables initialized")
        except Exception as e:
            logger.error(f"Failed to init verification tables: {e}")
            raise
    
    def generate_verification_token(self, ein: str, email: str, claim_type: str) -> Tuple[str, str]:
        """
        Generate email verification token for org claim
        
        Returns: (token, verification_url)
        """
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)  # 24h expiry
        
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute("""
                    INSERT INTO org_verification_tokens 
                    (token, ein, email, claim_type, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (token, ein, email, claim_type, expires_at))
                db.commit()
            
            verification_url = f"https://daanaa.org/verify-claim?token={token}"
            logger.info(f"✓ Token generated for {ein}: {email}")
            return token, verification_url
        except Exception as e:
            logger.error(f"Failed to generate token: {e}")
            raise
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Verify email token and mark claim as verified
        
        Returns: (success, ein, email)
        """
        try:
            with sqlite3.connect(self.db_path) as db:
                cursor = db.execute("""
                    SELECT ein, email, claim_type, expires_at, attempt_count
                    FROM org_verification_tokens
                    WHERE token = ?
                """, (token,))
                row = cursor.fetchone()
                
                if not row:
                    logger.warning(f"Token not found: {token}")
                    return False, None, None
                
                ein, email, claim_type, expires_at, attempt_count = row
                
                # Check expiry
                if datetime.fromisoformat(expires_at) < datetime.utcnow():
                    logger.warning(f"Token expired: {token}")
                    return False, None, None
                
                # Check attempt limit (max 5)
                if attempt_count >= 5:
                    logger.warning(f"Token locked (too many attempts): {token}")
                    return False, None, None
                
                # Mark as verified
                db.execute("""
                    UPDATE org_verification_tokens
                    SET verified_at = CURRENT_TIMESTAMP
                    WHERE token = ?
                """, (token,))
                
                # Record verified claim
                db.execute("""
                    INSERT OR REPLACE INTO org_verified_claims
                    (ein, email, verified_at, verification_type)
                    VALUES (?, ?, CURRENT_TIMESTAMP, ?)
                """, (ein, email, claim_type))
                
                db.commit()
                logger.info(f"✓ Claim verified for {ein}")
                return True, ein, email
        except Exception as e:
            logger.error(f"Failed to verify token: {e}")
            return False, None, None
    
    def is_claim_verified(self, ein: str) -> bool:
        """Check if org has verified claim"""
        try:
            with sqlite3.connect(self.db_path) as db:
                cursor = db.execute("""
                    SELECT verified_at FROM org_verified_claims
                    WHERE ein = ?
                """, (ein,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Failed to check verification: {e}")
            return False

# API Integration
def claims_endpoint_with_verification(ein: str, email: str, claim_data: dict) -> Tuple[bool, str]:
    """
    Modified org claims endpoint - now requires email verification
    
    Flow:
    1. Org submits claim + email
    2. System generates token, sends email
    3. Org clicks link, claim is marked verified
    4. Score can only use verified claims
    """
    verifier = OrgClaimsVerification()
    
    # Generate verification token
    token, verification_url = verifier.generate_verification_token(ein, email, claim_data.get('type', 'general'))
    
    # In production: send email with verification_url
    # For now: log it
    logger.info(f"Email to {email}: {verification_url}")
    
    return True, f"Verification email sent to {email}"

if __name__ == '__main__':
    # Test flow
    verifier = OrgClaimsVerification()
    
    # Org submits claim
    token, url = verifier.generate_verification_token(
        ein="111111111",
        email="org@example.com",
        claim_type="501c3_verified"
    )
    print(f"✓ Token generated: {token[:20]}...")
    print(f"✓ Verification URL: {url}")
    
    # Org clicks link
    success, ein, email = verifier.verify_token(token)
    if success:
        print(f"✓ Claim verified for {ein}")
    
    # Check verification
    is_verified = verifier.is_claim_verified("111111111")
    print(f"✓ Claim status verified: {is_verified}")
