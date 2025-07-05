"""
LinkedIn Post Extractor - Constants and Configuration

This module contains all constants, configuration values, and selectors used
throughout the LinkedIn Post Extractor application.
"""

import re
from typing import Dict, List

# Application Information
APP_NAME = "LinkedIn Post Extractor"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Extract posts from LinkedIn profiles and save as Markdown files"

# LinkedIn URL Patterns
LINKEDIN_PROFILE_PATTERNS = [
    r"^https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-]+/?$",
    r"^https?://(?:www\.)?linkedin\.com/pub/[a-zA-Z0-9\-/]+/?$",
    r"^https?://(?:www\.)?linkedin\.com/profile/view\?id=\d+$",
]

# Compiled regex patterns for URL validation
LINKEDIN_URL_REGEX = [re.compile(pattern) for pattern in LINKEDIN_PROFILE_PATTERNS]

# LinkedIn Domains
LINKEDIN_DOMAINS = [
    "linkedin.com",
    "www.linkedin.com",
]

# CSS Selectors for LinkedIn Post Extraction
# Note: These selectors may need updates if LinkedIn changes their HTML structure
LINKEDIN_SELECTORS = {
    # Post container selectors
    "post_container": [
        "div[data-id]",  # Main post container
        ".feed-shared-update-v2",  # Alternative post container
        ".activity-item",  # Activity feed item
    ],
    
    # Post content selectors
    "post_content": [
        ".feed-shared-text__text-view",  # Main post text
        ".activity-item__description",  # Activity description
        ".share-update-card__update-text",  # Update text
    ],
    
    # Post metadata selectors
    "post_date": [
        ".feed-shared-actor__sub-description time",  # Post timestamp
        ".activity-item__time",  # Activity timestamp
        "time[datetime]",  # Generic time element
    ],
    
    # Author information
    "author_name": [
        ".feed-shared-actor__title",  # Author name in feed
        ".activity-item__actor-name",  # Author name in activity
    ],
    
    # Load more content selectors
    "load_more_button": [
        "button[aria-label*='more']",  # Generic load more button
        ".feed-shared-text__see-more-link",  # See more link
    ],
    
    # Activity/posts section
    "activity_section": [
        "#experience-section",  # Main activity section
        ".pv-profile-section__section-info",  # Profile section info
        ".feed-container",  # Feed container
    ],
}

# Wait times and timeouts (in seconds)
TIMEOUTS = {
    "page_load": 30,  # Maximum time to wait for page load
    "element_wait": 10,  # Maximum time to wait for element to appear
    "scroll_pause": 2,  # Pause between scroll actions
    "network_timeout": 60,  # Network request timeout
    "implicit_wait": 10,  # Implicit wait time for elements
    "explicit_wait": 15,  # Explicit wait time for elements
    "page_load_timeout": 30,  # Page load timeout
}

# Selenium WebDriver Configuration
WEBDRIVER_CONFIG = {
    "headless": True,  # Run browser in headless mode by default
    "window_size": (1920, 1080),  # Browser window size
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "implicit_wait": 10,  # Implicit wait time for elements
}

# File and Output Configuration
OUTPUT_CONFIG = {
    "default_output_dir": "output",  # Default output directory
    "filename_template": "{profile_name}-posts-{date}.md",  # Output filename template
    "date_format": "%Y-%m-%d",  # Date format for filenames
    "encoding": "utf-8",  # File encoding
    "max_filename_length": 200,  # Maximum filename length
}

# Markdown Template Configuration
MARKDOWN_TEMPLATE = {
    "header": """# LinkedIn Posts - {profile_name}

**Extraction Date**: {extraction_date}
**Profile URL**: {profile_url}
**Total Posts**: {total_posts}

---

""",
    "post_template": """## Post {post_number}
**Date**: {post_date}
**Content**:
{post_content}

---

""",
    "empty_profile_template": """# LinkedIn Posts - {profile_name}

**Extraction Date**: {extraction_date}
**Profile URL**: {profile_url}
**Status**: No posts found

This profile appears to have no public posts available for extraction.

""",
}

# Error Messages
ERROR_MESSAGES = {
    "invalid_url": "Invalid LinkedIn profile URL. Please provide a valid LinkedIn profile URL.",
    "profile_not_found": "LinkedIn profile not found or is not accessible.",
    "no_posts": "No posts found on this LinkedIn profile.",
    "network_error": "Network error occurred while accessing LinkedIn. Please check your internet connection.",
    "parsing_error": "Error occurred while parsing LinkedIn page content.",
    "file_write_error": "Error occurred while writing output file.",
    "browser_error": "Error occurred while setting up or using web browser.",
}

# Success Messages
SUCCESS_MESSAGES = {
    "extraction_complete": "Post extraction completed successfully!",
    "file_saved": "Posts saved to: {filename}",
    "posts_extracted": "Successfully extracted {count} posts",
}

# Retry Configuration
RETRY_CONFIG = {
    "max_retries": 3,  # Maximum number of retry attempts
    "retry_delay": 5,  # Delay between retries in seconds
    "backoff_factor": 2,  # Exponential backoff factor
}

# Rate Limiting Configuration
RATE_LIMIT_CONFIG = {
    "requests_per_minute": 30,  # Maximum requests per minute
    "scroll_delay_min": 1,  # Minimum delay between scrolls
    "scroll_delay_max": 3,  # Maximum delay between scrolls
}

# Validation Patterns
VALIDATION_PATTERNS = {
    "profile_name": r"^[a-zA-Z0-9\-\s]+$",  # Valid profile name pattern
    "filename_safe": r"[<>:\"/\\|?*]",  # Characters to remove from filenames
}

# Browser User Agents (for rotation to avoid detection)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
]

# Debug Configuration
DEBUG_CONFIG = {
    "save_page_source": False,  # Save page source for debugging
    "screenshot_on_error": False,  # Take screenshot on errors
    "verbose_selectors": False,  # Log detailed selector matching
}
