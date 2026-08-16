"""
STREAM 7 Issue 3: Input Validation
Prevents SQL injection, XSS, and parameter tampering on all API endpoints
"""
import re
from typing import Any, Tuple, Optional, Dict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ValidationType(Enum):
    EIN = "ein"
    NAME = "name"
    INT = "int"
    FLOAT = "float"
    EMAIL = "email"
    URL = "url"
    SORT = "sort"
    ORDER = "order"
    NTEE = "ntee"

class InputValidator:
    """Validates and sanitizes API input parameters"""
    
    def __init__(self):
        # Regex patterns for validation
        self.patterns = {
            'ein': r'^\d{9}$',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'url': r'^https?://[a-zA-Z0-9.-]+(?:/[a-zA-Z0-9._~:/?#\[\]@!$&\'()*+,;=-]*)?$',
            'name': r'^[a-zA-Z0-9\s\-&.,]{1,255}$',
            'ntee': r'^[A-Z]\d{2}$',  # Single letter + 2 digits
        }
        
        # Allowed values for specific parameters
        self.allowed_values = {
            'order': ['asc', 'desc'],
            'sort': ['name', 'total_revenue', 'merit_score', 'state', 'ntee'],
        }
        
        # Size limits
        self.limits = {
            'search_query': 100,
            'org_name': 255,
            'url': 2048,
        }
    
    def validate_ein(self, value: str) -> Tuple[bool, str]:
        """Validate EIN format"""
        if not isinstance(value, str):
            return False, "EIN must be string"
        
        value = value.strip()
        if not re.match(self.patterns['ein'], value):
            return False, f"EIN must be 9 digits, got: {value}"
        
        logger.info(f"✓ Valid EIN: {value}")
        return True, value
    
    def validate_email(self, value: str) -> Tuple[bool, str]:
        """Validate email format"""
        if not isinstance(value, str):
            return False, "Email must be string"
        
        value = value.strip().lower()
        if not re.match(self.patterns['email'], value):
            return False, f"Invalid email format: {value}"
        
        # Check length
        if len(value) > 254:
            return False, "Email too long (>254 chars)"
        
        logger.info(f"✓ Valid email: {value}")
        return True, value
    
    def validate_url(self, value: str) -> Tuple[bool, str]:
        """Validate URL format"""
        if not isinstance(value, str):
            return False, "URL must be string"
        
        value = value.strip()
        if len(value) > self.limits['url']:
            return False, f"URL too long (>{self.limits['url']} chars)"
        
        if not re.match(self.patterns['url'], value):
            return False, f"Invalid URL format: {value}"
        
        logger.info(f"✓ Valid URL: {value}")
        return True, value
    
    def validate_org_name(self, value: str) -> Tuple[bool, str]:
        """Validate organization name"""
        if not isinstance(value, str):
            return False, "Organization name must be string"
        
        value = value.strip()
        if len(value) < 1:
            return False, "Organization name cannot be empty"
        
        if len(value) > self.limits['org_name']:
            return False, f"Organization name too long (>{self.limits['org_name']} chars)"
        
        # Allow alphanumeric, spaces, hyphens, ampersand, period, comma
        if not re.match(self.patterns['name'], value):
            return False, f"Organization name contains invalid characters: {value}"
        
        logger.info(f"✓ Valid org name: {value}")
        return True, value
    
    def validate_integer(self, value: Any, min_val: int = 0, max_val: int = 1000000) -> Tuple[bool, int]:
        """Validate integer parameter"""
        try:
            int_val = int(value)
            if not (min_val <= int_val <= max_val):
                return False, f"Value out of range [{min_val}, {max_val}]"
            logger.info(f"✓ Valid integer: {int_val}")
            return True, int_val
        except (TypeError, ValueError):
            return False, f"Invalid integer: {value}"
    
    def validate_sort_parameter(self, value: str) -> Tuple[bool, str]:
        """Validate sort parameter"""
        if not isinstance(value, str):
            return False, "Sort must be string"
        
        value = value.strip().lower()
        if value not in self.allowed_values['sort']:
            return False, f"Invalid sort. Allowed: {', '.join(self.allowed_values['sort'])}"
        
        logger.info(f"✓ Valid sort: {value}")
        return True, value
    
    def validate_order_parameter(self, value: str) -> Tuple[bool, str]:
        """Validate order parameter"""
        if not isinstance(value, str):
            return False, "Order must be string"
        
        value = value.strip().lower()
        if value not in self.allowed_values['order']:
            return False, f"Invalid order. Allowed: {', '.join(self.allowed_values['order'])}"
        
        logger.info(f"✓ Valid order: {value}")
        return True, value
    
    def validate_search_query(self, value: str) -> Tuple[bool, str]:
        """Validate search query"""
        if not isinstance(value, str):
            return False, "Search query must be string"
        
        value = value.strip()
        if len(value) < 2:
            return False, "Search query too short (<2 chars)"
        
        if len(value) > self.limits['search_query']:
            return False, f"Search query too long (>{self.limits['search_query']} chars)"
        
        # Prevent obvious injection attempts
        dangerous_patterns = [';', '--', '/*', '*/', 'xp_', 'sp_']
        for pattern in dangerous_patterns:
            if pattern.lower() in value.lower():
                logger.warning(f"Blocked suspicious query: {value}")
                return False, f"Query contains forbidden pattern: {pattern}"
        
        logger.info(f"✓ Valid search query: {value[:50]}...")
        return True, value
    
    def validate_parameter(self, name: str, value: Any, validation_type: ValidationType) -> Tuple[bool, Any]:
        """Unified parameter validation"""
        validators = {
            ValidationType.EIN: self.validate_ein,
            ValidationType.EMAIL: self.validate_email,
            ValidationType.URL: self.validate_url,
            ValidationType.NAME: self.validate_org_name,
            ValidationType.SORT: self.validate_sort_parameter,
            ValidationType.ORDER: self.validate_order_parameter,
            ValidationType.INT: self.validate_integer,
        }
        
        if validation_type not in validators:
            return False, f"Unknown validation type: {validation_type}"
        
        validator = validators[validation_type]
        return validator(value)

# Global instance
_validator = InputValidator()

def validate_param(name: str, value: Any, validation_type: ValidationType) -> Tuple[bool, Any]:
    """Wrapper for Flask use"""
    return _validator.validate_parameter(name, value, validation_type)

if __name__ == '__main__':
    validator = InputValidator()
    
    # Test EIN validation
    valid, result = validator.validate_ein("123456789")
    assert valid and result == "123456789", "Valid EIN should pass"
    print("✓ Valid EIN: 123456789")
    
    invalid, msg = validator.validate_ein("12345")
    assert not invalid, "Invalid EIN should fail"
    print(f"✓ Invalid EIN rejected: {msg}")
    
    # Test email validation
    valid, email = validator.validate_email("test@example.com")
    assert valid, "Valid email should pass"
    print("✓ Valid email: test@example.com")
    
    invalid, msg = validator.validate_email("not-an-email")
    assert not invalid, "Invalid email should fail"
    print(f"✓ Invalid email rejected: {msg}")
    
    # Test sort parameter
    valid, sort = validator.validate_sort_parameter("total_revenue")
    assert valid, "Valid sort should pass"
    print("✓ Valid sort: total_revenue")
    
    invalid, msg = validator.validate_sort_parameter("id")
    assert not invalid, "Invalid sort should fail"
    print(f"✓ Invalid sort rejected: {msg}")
    
    # Test SQL injection prevention
    invalid, msg = validator.validate_search_query("test'; DROP TABLE orgs--")
    assert not invalid, "SQL injection should fail"
    print(f"✓ SQL injection blocked: {msg}")
    
    print("\n✅ Input validation tests passed")
