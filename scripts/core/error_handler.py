"""
STREAM 7 Issue 5: Stack Trace Suppression
Production mode suppresses internal stack traces, logs securely, returns safe errors
"""
import os
import sys
import traceback
import json
from datetime import datetime
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class ProductionErrorHandler:
    """Handles errors safely in production (suppress stack traces)"""
    
    def __init__(self, is_production: bool = None):
        """
        is_production: if None, read from DAANAA_PROD env var
        """
        if is_production is None:
            is_production = os.environ.get('DAANAA_PROD', '').lower() == 'true'
        
        self.is_production = is_production
        self.error_log = []  # In-memory buffer; in production use external logging
    
    def handle_api_error(self, error: Exception, endpoint: str, request_id: str) -> Tuple[int, Dict]:
        """
        Handle API error and return safe response
        
        Returns: (status_code, response_dict)
        """
        # Log full error securely (only in logs, not in response)
        error_id = self._generate_error_id(request_id)
        self._log_error(error, endpoint, error_id)
        
        if self.is_production:
            # Production: return generic error
            return 500, {
                "error": "Internal server error",
                "error_id": error_id,
                "message": "An error occurred. Please contact support with error ID above."
            }
        else:
            # Development: return full stack trace
            return 500, {
                "error": str(error),
                "error_id": error_id,
                "traceback": traceback.format_exc(),
                "endpoint": endpoint
            }
    
    def handle_validation_error(self, error_msg: str) -> Tuple[int, Dict]:
        """Handle input validation errors (safe to expose)"""
        return 400, {
            "error": "Validation error",
            "message": error_msg
        }
    
    def handle_not_found(self, resource: str) -> Tuple[int, Dict]:
        """Handle 404 errors"""
        return 404, {
            "error": "Not found",
            "message": f"{resource} not found"
        }
    
    def handle_auth_error(self) -> Tuple[int, Dict]:
        """Handle authentication errors (minimal info)"""
        return 401, {
            "error": "Unauthorized",
            "message": "Invalid or missing credentials"
        }
    
    def _log_error(self, error: Exception, endpoint: str, error_id: str):
        """Log error with full context to secure log"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_id": error_id,
            "endpoint": endpoint,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc()
        }
        
        # Log to secure logging (not stdout)
        logger.error(json.dumps(log_entry))
        
        # In-memory buffer (for testing)
        self.error_log.append(log_entry)
    
    @staticmethod
    def _generate_error_id(request_id: str) -> str:
        """Generate trackable error ID from request ID"""
        import hashlib
        return hashlib.sha256(f"{request_id}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:8]

# Global instance
_handler = None

def get_error_handler(is_production: bool = None) -> ProductionErrorHandler:
    """Get or create error handler"""
    global _handler
    if _handler is None:
        _handler = ProductionErrorHandler(is_production)
    return _handler

if __name__ == '__main__':
    # Test production mode
    handler = ProductionErrorHandler(is_production=True)
    
    try:
        raise ValueError("This is a test error")
    except Exception as e:
        status, response = handler.handle_api_error(e, "/api/test", "req_12345")
        
        assert status == 500, "Should return 500"
        assert "internal server error" in response["error"].lower(), "Should be generic in production"
        assert "traceback" not in response, "Should NOT include traceback in production"
        assert "error_id" in response, "Should include error ID for support"
        
        print(f"✓ Production mode: {response}")
    
    # Test dev mode
    handler = ProductionErrorHandler(is_production=False)
    
    try:
        raise ValueError("This is a test error")
    except Exception as e:
        status, response = handler.handle_api_error(e, "/api/test", "req_12345")
        
        assert "traceback" in response, "Should include traceback in dev mode"
        print(f"✓ Dev mode: Full traceback included")
    
    # Test validation errors
    status, response = handler.handle_validation_error("Invalid EIN format")
    assert status == 400, "Validation errors should return 400"
    assert "Validation error" in response["error"], "Should identify as validation error"
    print(f"✓ Validation error: {response}")
    
    # Test auth errors
    status, response = handler.handle_auth_error()
    assert status == 401, "Auth errors should return 401"
    assert "Invalid or missing credentials" in response["message"], "Should be generic"
    print(f"✓ Auth error: {response}")
    
    print("\n✅ Error handler tests passed")
