"""ISSUE 6 FIX: Error handler - CloudLogging + trace scrubbing"""
import os
import traceback
import json
from datetime import datetime, timezone
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class ProductionErrorHandler:
    """FIXED: CloudLogging integration + trace scrubbing"""
    
    def __init__(self, is_production: bool = None):
        self.is_production = is_production or (os.environ.get('DAANAA_PROD', '').lower() == 'true')
        self.error_log = []
        
        # CloudLogging setup (production only)
        if self.is_production:
            try:
                from google.cloud import logging as cloud_logging
                client = cloud_logging.Client()
                self.cloud_logger = client.logger("daanaa-api-errors")
                logger.info("✓ CloudLogging initialized")
            except Exception as e:
                logger.warning(f"CloudLogging unavailable: {e}; falling back to local logging")
                self.cloud_logger = None
        else:
            self.cloud_logger = None
    
    def handle_api_error(self, error: Exception, endpoint: str, request_id: str) -> Tuple[int, Dict]:
        """Handle API error; log securely, return safe response"""
        error_id = self._generate_error_id(request_id)
        self._log_error(error, endpoint, error_id)
        
        if self.is_production:
            return 500, {
                "error": "Internal server error",
                "error_id": error_id,
                "message": "Please contact support with error ID."
            }
        else:
            return 500, {
                "error": str(error),
                "error_id": error_id,
                "traceback": traceback.format_exc(),
                "endpoint": endpoint
            }
    
    def _log_error(self, error: Exception, endpoint: str, error_id: str):
        """FIXED: Log to CloudLogging with scrubbed traceback"""
        trace_str = traceback.format_exc()
        
        # Scrub traceback (remove local variable values)
        if self.is_production:
            trace_str = self._scrub_traceback(trace_str)
        
        log_entry = {
            "error_id": error_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint": endpoint,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": trace_str
        }
        
        if self.cloud_logger:
            self.cloud_logger.error(json.dumps(log_entry))
        else:
            logger.error(json.dumps(log_entry))
        
        self.error_log.append(log_entry)
    
    @staticmethod
    def _scrub_traceback(trace_str: str) -> str:
        """FIXED: Remove local variable values from traceback"""
        lines = trace_str.split('\n')
        scrubbed = []
        skip_next = False
        
        for line in lines:
            if line.strip().startswith('Local variables at frame'):
                skip_next = True
                continue
            if skip_next:
                if line.strip() == '':
                    skip_next = False
                continue
            scrubbed.append(line)
        
        return '\n'.join(scrubbed)
    
    @staticmethod
    def _generate_error_id(request_id: str) -> str:
        """FIXED: 16-char error ID (collision resistant)"""
        import hashlib
        return hashlib.sha256(f"{request_id}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:16]

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    handler = ProductionErrorHandler(is_production=True)
    
    try:
        raise ValueError("Test error")
    except Exception as e:
        status, response = handler.handle_api_error(e, "/api/test", "req_12345")
        assert status == 500
        assert "internal server error" in response["error"].lower()
        assert len(response["error_id"]) == 16, "Error ID should be 16 chars"
        print("✓ Production mode: generic error, 16-char ID")
    
    print("✅ Error handler v2 verified")
