"""
STREAM 7 Issue 6: Analytics Privacy Verification
Ensures Plausible analytics respects privacy-first principles
- No PII in events
- No user tracking
- No third-party cookies
"""
import re
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)

class AnalyticsPrivacyValidator:
    """Validates analytics events for privacy compliance"""
    
    def __init__(self):
        # Patterns for detecting PII
        self.pii_patterns = {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'ein': r'\b\d{2}-\d{7}\b',  # With dashes
            'zip_code': r'\b\d{5}(?:-\d{4})?\b'  # Partial - flagged if not intentional
        }
        
        # Allowed field names (safe for analytics)
        self.allowed_fields = {
            'page', 'referrer', 'screen_width', 'screen_height',
            'device_type', 'browser', 'os', 'country', 'event_name',
            'event_type', 'timestamp', 'session_duration', 'bounce_rate'
        }
        
        # Blocked field names (never send these)
        self.blocked_fields = {
            'user_id', 'uid', 'session_id', 'userid', 'customer_id',
            'email', 'phone', 'address', 'ssn', 'credit_card',
            'password', 'auth_token', 'api_key', 'secret'
        }
    
    def validate_event(self, event: Dict) -> Tuple[bool, List[str]]:
        """
        Validate analytics event for privacy compliance
        
        Returns: (is_valid, list_of_issues)
        """
        issues = []
        
        # Check for blocked field names
        for field_name in event.keys():
            if field_name.lower() in self.blocked_fields:
                issues.append(f"Blocked field: {field_name}")
                logger.warning(f"⚠️  Blocked field in analytics event: {field_name}")
        
        # Check for PII in values
        for field_name, value in event.items():
            if isinstance(value, str):
                for pii_type, pattern in self.pii_patterns.items():
                    if re.search(pattern, value):
                        # Special case: zip_code is allowed if field is "country" or "region"
                        if pii_type == 'zip_code' and field_name in ['country', 'region']:
                            continue
                        
                        issues.append(f"Potential {pii_type} in field '{field_name}'")
                        logger.warning(f"⚠️  Potential {pii_type} detected in analytics event")
        
        # Check page URL for PII
        if 'page' in event:
            page = event['page']
            # Check for email/id in URL parameters
            if '?' in page:
                query_string = page.split('?')[1]
                if any(x in query_string.lower() for x in ['email', 'id', 'user', 'token', 'key']):
                    issues.append("Potential PII in URL parameters")
                    logger.warning("⚠️  Potential PII in URL parameters")
        
        # Check that user_id is NOT sent (critical)
        if any(key.lower() in ['user_id', 'uid', 'userid'] for key in event.keys()):
            issues.append("User ID must not be sent to analytics")
            logger.error("🚨 User ID attempted to send to analytics (BLOCKED)")
        
        is_valid = len(issues) == 0
        if is_valid:
            logger.info(f"✓ Analytics event valid: {event.get('event_name', 'unknown')}")
        
        return is_valid, issues
    
    def sanitize_url(self, url: str) -> str:
        """Remove PII from URL before sending to analytics"""
        # Remove common PII parameters
        pii_params = ['email', 'user_id', 'uid', 'token', 'api_key', 'password']
        
        for param in pii_params:
            # Remove ?param=value or &param=value
            url = re.sub(rf'[?&]{param}=[^&]*', '', url)
        
        return url
    
    def get_safe_page_view_event(self, page_url: str) -> Dict:
        """Create a safe pageview event (scrubbed of PII)"""
        safe_url = self.sanitize_url(page_url)
        return {
            'event_name': 'pageview',
            'page': safe_url,
            # No user tracking
            # No session ID
            # No personal data
        }
    
    def get_safe_search_event(self, query: str, result_count: int) -> Dict:
        """Create a safe search event (no query tracking)"""
        # NEVER send the search query itself (it could be PII)
        return {
            'event_name': 'search',
            'result_count': result_count,
            'search_category': 'organizations',  # Generic category only
            # No query text
            # No user identifier
        }

# Global instance
_validator = AnalyticsPrivacyValidator()

def validate_analytics_event(event: Dict) -> Tuple[bool, List[str]]:
    """Wrapper for use in analytics tracking"""
    return _validator.validate_event(event)

def sanitize_page_url(url: str) -> str:
    """Sanitize URL before sending to Plausible"""
    return _validator.sanitize_url(url)

if __name__ == '__main__':
    validator = AnalyticsPrivacyValidator()
    
    # Test valid event
    valid_event = {'event_name': 'pageview', 'page': '/directory'}
    is_valid, issues = validator.validate_event(valid_event)
    assert is_valid, "Valid event should pass"
    print(f"✓ Valid event: {valid_event}")
    
    # Test event with PII (email)
    pii_event = {'event_name': 'signup', 'email': 'user@example.com'}
    is_valid, issues = validator.validate_event(pii_event)
    assert not is_valid, "Event with email should fail"
    print(f"✓ PII detected: {issues}")
    
    # Test event with blocked field
    blocked_event = {'user_id': '12345', 'page': '/'}
    is_valid, issues = validator.validate_event(blocked_event)
    assert not is_valid, "Event with user_id should fail"
    print(f"✓ Blocked field detected: {issues}")
    
    # Test URL sanitization
    dirty_url = "https://daanaa.org/search?q=homeless%20services&user_id=abc123&token=xyz"
    clean_url = validator.sanitize_url(dirty_url)
    assert 'user_id' not in clean_url and 'token' not in clean_url, "Should remove PII params"
    print(f"✓ URL sanitized: {dirty_url} → {clean_url}")
    
    # Test safe pageview
    safe_pageview = validator.get_safe_page_view_event("https://daanaa.org/org/123456789")
    is_valid, issues = validator.validate_event(safe_pageview)
    assert is_valid, "Safe pageview should pass"
    print(f"✓ Safe pageview event: {safe_pageview}")
    
    # Test safe search event (no query text)
    safe_search = validator.get_safe_search_event("homeless services", 45)
    assert 'homeless' not in str(safe_search).lower(), "Query should NOT be in event"
    is_valid, issues = validator.validate_event(safe_search)
    assert is_valid, "Safe search should pass"
    print(f"✓ Safe search event (query hidden): {safe_search}")
    
    print("\n✅ Analytics privacy tests passed")
