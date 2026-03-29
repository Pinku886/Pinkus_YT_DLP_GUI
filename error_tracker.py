"""
Error Tracker Module
Handles persistent storage of failed download URLs
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class ErrorTracker:
    def __init__(self):
        """Initialize error tracker with path to error storage file"""
        self.error_file = os.path.join(
            os.getenv('APPDATA'), 'yt-dlp', 'failed_urls.json'
        )
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create error file if it doesn't exist"""
        if not os.path.exists(self.error_file):
            folder = os.path.dirname(self.error_file)
            if not os.path.exists(folder):
                os.makedirs(folder)
            self._write_errors([])
    
    def _read_errors(self) -> List[Dict]:
        """Read errors from JSON file"""
        try:
            with open(self.error_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _write_errors(self, errors: List[Dict]):
        """Write errors to JSON file"""
        try:
            with open(self.error_file, 'w', encoding='utf-8') as f:
                json.dump(errors, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing to error file: {e}")
    
    def add_error(self, url: str, error_msg: str, context: str = ""):
        """
        Add a failed URL to the error tracker
        
        Args:
            url: The URL that failed
            error_msg: Error message/description
            context: Additional context (e.g., "Main Download", "Batch Download")
        """
        errors = self._read_errors()
        
        # Check if URL already exists, update it
        existing = None
        for err in errors:
            if err.get('url') == url:
                existing = err
                break
        
        if existing:
            # Update existing error
            existing['error'] = error_msg
            existing['context'] = context
            existing['timestamp'] = datetime.now().isoformat()
            existing['retry_count'] = existing.get('retry_count', 0) + 1
        else:
            # Add new error
            error_entry = {
                'url': url,
                'error': error_msg,
                'context': context,
                'timestamp': datetime.now().isoformat(),
                'retry_count': 0
            }
            errors.append(error_entry)
        
        self._write_errors(errors)
    
    def get_errors(self) -> List[Dict]:
        """Get all errors"""
        return self._read_errors()
    
    def get_error_count(self) -> int:
        """Get count of failed URLs"""
        return len(self._read_errors())
    
    def remove_error(self, url: str):
        """Remove a specific error by URL"""
        errors = self._read_errors()
        errors = [e for e in errors if e.get('url') != url]
        self._write_errors(errors)
    
    def clear_all_errors(self):
        """Clear all errors"""
        self._write_errors([])
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return self.get_error_count() > 0
