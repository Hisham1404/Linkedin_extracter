"""
LinkedIn Post Extractor - URL Validation Module

This module provides comprehensive LinkedIn URL validation functionality including:
- LinkedIn profile URL pattern validation
- URL accessibility checks
- Format normalization and cleaning
- Support for various LinkedIn URL formats
"""

import re
import requests
from typing import Optional, Tuple, List
from urllib.parse import urlparse, urlunparse
import logging

from config import (
    LINKEDIN_URL_REGEX, 
    LINKEDIN_DOMAINS, 
    ERROR_MESSAGES,
    TIMEOUTS
)

logger = logging.getLogger(__name__)


class LinkedInURLValidator:
    """
    Validates and processes LinkedIn profile URLs.
    
    Supports various LinkedIn URL formats:
    - https://www.linkedin.com/in/username
    - https://linkedin.com/in/username
    - https://www.linkedin.com/pub/firstname-lastname/123/456/789
    - https://www.linkedin.com/profile/view?id=123456789
    """
    
    def __init__(self):
        self.compiled_patterns = LINKEDIN_URL_REGEX
        self.valid_domains = LINKEDIN_DOMAINS
        
    def validate_url_format(self, url: str) -> Tuple[bool, str]:
        """
        Validate if the URL matches LinkedIn profile URL patterns.
        
        Args:
            url: URL string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url or not isinstance(url, str):
            return False, "URL cannot be empty"
            
        url = url.strip()
        
        # Basic URL structure validation
        try:
            parsed = urlparse(url)
            if not parsed.scheme:
                # Try adding https:// if no scheme provided
                url = f"https://{url}"
                parsed = urlparse(url)
                
            if not parsed.netloc:
                return False, "Invalid URL format"
                
        except Exception as e:
            logger.debug(f"URL parsing error: {e}")
            return False, "Invalid URL format"
        
        # Check if domain is LinkedIn
        domain = parsed.netloc.lower()
        if domain not in self.valid_domains:
            return False, f"URL must be from LinkedIn domain ({', '.join(self.valid_domains)})"
        
        # Check against LinkedIn URL patterns
        for pattern in self.compiled_patterns:
            if pattern.match(url):
                logger.debug(f"URL matched pattern: {pattern.pattern}")
                return True, ""
                
        return False, ERROR_MESSAGES["invalid_url"]
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize LinkedIn URL to standard format.
        
        Args:
            url: LinkedIn URL to normalize
            
        Returns:
            Normalized URL string
        """
        url = url.strip()
        
        # Add https:// if no scheme
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
            
        # Parse and rebuild URL
        parsed = urlparse(url)
        
        # Ensure www. prefix for consistency
        netloc = parsed.netloc.lower()
        if netloc == 'linkedin.com':
            netloc = 'www.linkedin.com'
            
        # Remove trailing slash from path
        path = parsed.path.rstrip('/')
        
        # Rebuild URL
        normalized = urlunparse((
            'https',  # Always use HTTPS
            netloc,
            path,
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))
        
        logger.debug(f"Normalized URL: {url} -> {normalized}")
        return normalized
    
    def check_url_accessibility(self, url: str) -> Tuple[bool, str]:
        """
        Check if the LinkedIn URL is accessible (returns 200 status).
        
        Args:
            url: LinkedIn URL to check
            
        Returns:
            Tuple of (is_accessible, error_message)
        """
        try:
            # Use HEAD request to avoid downloading full page
            response = requests.head(
                url,
                timeout=TIMEOUTS["network_timeout"],
                allow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
            
            if response.status_code == 200:
                logger.debug(f"URL accessible: {url}")
                return True, ""
            elif response.status_code == 404:
                return False, ERROR_MESSAGES["profile_not_found"]
            elif response.status_code == 403:
                return False, "Profile access denied or private profile"
            else:
                return False, f"HTTP {response.status_code}: Unable to access profile"
                
        except requests.exceptions.Timeout:
            return False, "Request timeout - please check your internet connection"
        except requests.exceptions.ConnectionError:
            return False, ERROR_MESSAGES["network_error"]
        except requests.exceptions.RequestException as e:
            logger.debug(f"Request error: {e}")
            return False, "Unable to verify profile accessibility"
    
    def validate_and_normalize(self, url: str, check_accessibility: bool = True) -> Tuple[bool, str, str]:
        """
        Complete validation and normalization of LinkedIn URL.
        
        Args:
            url: LinkedIn URL to validate
            check_accessibility: Whether to check if URL is accessible online
            
        Returns:
            Tuple of (is_valid, normalized_url, error_message)
        """
        # Step 1: Format validation
        is_valid_format, format_error = self.validate_url_format(url)
        if not is_valid_format:
            return False, url, format_error
            
        # Step 2: Normalize URL
        try:
            normalized_url = self.normalize_url(url)
        except Exception as e:
            logger.error(f"URL normalization error: {e}")
            return False, url, "Error processing URL format"
            
        # Step 3: Accessibility check (optional)
        if check_accessibility:
            is_accessible, access_error = self.check_url_accessibility(normalized_url)
            if not is_accessible:
                return False, normalized_url, access_error
                
        return True, normalized_url, ""


def validate_linkedin_url(url: str, check_accessibility: bool = True) -> Tuple[bool, str, str]:
    """
    Convenience function for LinkedIn URL validation.
    
    Args:
        url: LinkedIn URL to validate
        check_accessibility: Whether to check online accessibility
        
    Returns:
        Tuple of (is_valid, normalized_url, error_message)
    """
    validator = LinkedInURLValidator()
    return validator.validate_and_normalize(url, check_accessibility)


def get_profile_username(url: str) -> Optional[str]:
    """
    Extract username/identifier from LinkedIn profile URL.
    
    Args:
        url: LinkedIn profile URL
        
    Returns:
        Username string or None if not extractable
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        # Handle /in/username format
        if path.startswith('in/'):
            username = path.split('/')[-1]
            return username if username else None
            
        # Handle /pub/name/numbers format
        if path.startswith('pub/'):
            parts = path.split('/')
            if len(parts) >= 2:
                return parts[1]  # Return the name part
                
        # Handle profile view format
        if 'profile/view' in path and parsed.query:
            # Extract ID from query params
            import urllib.parse
            query_params = urllib.parse.parse_qs(parsed.query)
            profile_id = query_params.get('id', [None])[0]
            return profile_id
            
        logger.debug(f"Could not extract username from URL: {url}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting username from URL {url}: {e}")
        return None


def suggest_url_corrections(invalid_url: str) -> List[str]:
    """
    Suggest possible corrections for invalid LinkedIn URLs.
    
    Args:
        invalid_url: The invalid URL string
        
    Returns:
        List of suggested corrected URLs
    """
    suggestions = []
    
    # Clean the input
    cleaned = invalid_url.strip().lower()
    
    # Remove common prefixes that users might add incorrectly
    cleaned = re.sub(r'^(https?://)?', '', cleaned)
    cleaned = re.sub(r'^(www\.)?', '', cleaned)
    
    # If it looks like just a username, suggest full URL
    if re.match(r'^[a-zA-Z0-9\-]+$', cleaned):
        suggestions.append(f"https://www.linkedin.com/in/{cleaned}")
        
    # If it contains linkedin but missing parts
    if 'linkedin' in cleaned:
        # Handle linkedin.com/username format
        if cleaned.startswith('linkedin.com/'):
            username = cleaned.replace('linkedin.com/', '')
            if username and not username.startswith('in/'):
                suggestions.append(f"https://www.linkedin.com/in/{username}")
        else:
            # Try to extract potential username from other linkedin patterns
            match = re.search(r'linkedin(?:\.com)?(?:/in/)?/?([a-zA-Z0-9\-]+)', cleaned)
            if match:
                username = match.group(1)
                suggestions.append(f"https://www.linkedin.com/in/{username}")
            
    # Add common corrections
    if cleaned and not any(suggestions):
        # Assume it's a username and suggest standard format
        safe_username = re.sub(r'[^a-zA-Z0-9\-]', '', cleaned)
        if safe_username:
            suggestions.append(f"https://www.linkedin.com/in/{safe_username}")
    
    return suggestions[:3]  # Return max 3 suggestions
