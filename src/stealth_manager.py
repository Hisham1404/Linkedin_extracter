"""
LinkedIn Post Extractor - Stealth Module

This module provides advanced anti-bot detection bypass techniques for LinkedIn scraping.
It includes proxy support, user agent rotation, request timing, and other stealth techniques.
"""

import time
import random
import requests
from typing import Optional, Dict, List, Tuple
import logging
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.chrome.options import Options as ChromeOptions

from config import USER_AGENTS, ANTI_BOT_CONFIG

logger = logging.getLogger(__name__)


class StealthManager:
    """
    Manages stealth techniques to avoid LinkedIn's anti-bot detection.
    """
    
    def __init__(self, use_proxy: bool = False, proxy_list: Optional[List[str]] = None):
        """
        Initialize stealth manager.
        
        Args:
            use_proxy: Whether to use proxy rotation
            proxy_list: List of proxy servers (format: "ip:port" or "ip:port:username:password")
        """
        self.use_proxy = use_proxy
        self.proxy_list = proxy_list or []
        self.current_proxy_index = 0
        self.user_agent_index = 0
        self.last_request_time = 0
        
    def get_random_user_agent(self) -> str:
        """
        Get a random user agent from the pool.
        
        Returns:
            Random user agent string
        """
        return random.choice(USER_AGENTS)
        
    def get_next_user_agent(self) -> str:
        """
        Get the next user agent in rotation.
        
        Returns:
            Next user agent string
        """
        user_agent = USER_AGENTS[self.user_agent_index]
        self.user_agent_index = (self.user_agent_index + 1) % len(USER_AGENTS)
        return user_agent
        
    def wait_random_delay(self, min_delay: Optional[float] = None, max_delay: Optional[float] = None):
        """
        Wait for a random delay to mimic human behavior.
        
        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        min_delay = min_delay or ANTI_BOT_CONFIG["min_delay_between_requests"]
        max_delay = max_delay or ANTI_BOT_CONFIG["max_delay_between_requests"]
        
        delay = random.uniform(min_delay, max_delay)
        logger.debug(f"Waiting {delay:.2f} seconds for stealth delay")
        time.sleep(delay)
        
    def should_wait_for_rate_limit(self) -> bool:
        """
        Check if we should wait to avoid rate limiting.
        
        Returns:
            True if we should wait, False otherwise
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < ANTI_BOT_CONFIG["min_delay_between_requests"]:
            return True
            
        return False
        
    def apply_rate_limiting(self):
        """
        Apply rate limiting by waiting if necessary.
        """
        if self.should_wait_for_rate_limit():
            wait_time = ANTI_BOT_CONFIG["min_delay_between_requests"] - (time.time() - self.last_request_time)
            if wait_time > 0:
                logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
                
        self.last_request_time = time.time()
        
    def get_stealth_headers(self) -> Dict[str, str]:
        """
        Get headers that mimic a real browser request.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"'
        }
        
    def get_current_proxy(self) -> Optional[str]:
        """
        Get the current proxy server.
        
        Returns:
            Current proxy string or None if no proxy
        """
        if not self.use_proxy or not self.proxy_list:
            return None
            
        return self.proxy_list[self.current_proxy_index]
        
    def rotate_proxy(self):
        """
        Rotate to the next proxy server.
        """
        if self.proxy_list:
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
            logger.debug(f"Rotated to proxy: {self.get_current_proxy()}")
            
    def configure_proxy_for_selenium(self, options: ChromeOptions) -> ChromeOptions:
        """
        Configure proxy settings for Selenium WebDriver.
        
        Args:
            options: Chrome options to configure
            
        Returns:
            Modified Chrome options with proxy settings
        """
        if not self.use_proxy or not self.proxy_list:
            return options
            
        proxy_string = self.get_current_proxy()
        if not proxy_string:
            return options
            
        # Parse proxy string
        proxy_parts = proxy_string.split(':')
        if len(proxy_parts) >= 2:
            proxy_host = proxy_parts[0]
            proxy_port = proxy_parts[1]
            
            # Add proxy arguments
            options.add_argument(f'--proxy-server=http://{proxy_host}:{proxy_port}')
            
            # If username and password are provided
            if len(proxy_parts) == 4:
                proxy_username = proxy_parts[2]
                proxy_password = proxy_parts[3]
                logger.debug(f"Configured authenticated proxy: {proxy_host}:{proxy_port}")
            else:
                logger.debug(f"Configured proxy: {proxy_host}:{proxy_port}")
                
        return options
        
    def make_stealth_request(self, url: str, method: str = 'GET', **kwargs) -> requests.Response:
        """
        Make a request with stealth techniques applied.
        
        Args:
            url: Target URL
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
        """
        # Apply rate limiting
        self.apply_rate_limiting()
        
        # Set up session with stealth headers
        session = requests.Session()
        session.headers.update(self.get_stealth_headers())
        
        # Configure proxy if available
        if self.use_proxy and self.proxy_list:
            proxy_string = self.get_current_proxy()
            if proxy_string:
                proxy_parts = proxy_string.split(':')
                if len(proxy_parts) >= 2:
                    proxy_dict = {
                        'http': f'http://{proxy_string}',
                        'https': f'https://{proxy_string}'
                    }
                    session.proxies.update(proxy_dict)
                    
        # Set default timeout
        kwargs.setdefault('timeout', ANTI_BOT_CONFIG["request_timeout"])
        
        # Make request
        response = session.request(method, url, **kwargs)
        
        # Handle specific LinkedIn anti-bot responses
        if response.status_code == 999:
            logger.warning("LinkedIn anti-bot protection detected (HTTP 999)")
            # Wait longer before next request
            time.sleep(ANTI_BOT_CONFIG["retry_after_999"])
            
        elif response.status_code == 429:
            logger.warning("Rate limit exceeded (HTTP 429)")
            time.sleep(ANTI_BOT_CONFIG["retry_after_429"])
            
        elif response.status_code == 403:
            logger.warning("Access forbidden (HTTP 403)")
            time.sleep(ANTI_BOT_CONFIG["retry_after_403"])
            
        return response
        
    def get_javascript_stealth_code(self) -> str:
        """
        Get JavaScript code to execute for stealth purposes.
        
        Returns:
            JavaScript code string
        """
        return """
        // Hide webdriver property
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        
        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Override permissions
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: () => Promise.resolve({state: 'granted'})
            })
        });
        
        // Override chrome object
        window.navigator.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {}
        };
        
        // Override notification permission (with safety check)
        if (typeof Notification !== 'undefined') {
            Object.defineProperty(Notification, 'permission', {
                get: () => 'granted'
            });
        }
        
        // Override screen properties
        Object.defineProperty(screen, 'colorDepth', {get: () => 24});
        Object.defineProperty(screen, 'pixelDepth', {get: () => 24});
        
        // Hide automation indicators
        delete navigator.__proto__.webdriver;
        """


def create_stealth_manager(use_proxy: bool = False, proxy_list: Optional[List[str]] = None) -> StealthManager:
    """
    Create a configured stealth manager instance.
    
    Args:
        use_proxy: Whether to enable proxy rotation
        proxy_list: List of proxy servers
        
    Returns:
        Configured StealthManager instance
    """
    return StealthManager(use_proxy=use_proxy, proxy_list=proxy_list)
