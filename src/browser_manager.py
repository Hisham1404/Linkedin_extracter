"""
LinkedIn Post Extractor - WebDriver Manager Module

This module provides comprehensive web automation capabilities using Selenium WebDriver
for LinkedIn post extraction. It handles browser initialization, configuration, and
provides methods for navigation and element interaction.
"""

import os
import time
import random
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
    SessionNotCreatedException
)
from webdriver_manager.chrome import ChromeDriverManager
import logging

from config import (
    WEBDRIVER_CONFIG,
    TIMEOUTS,
    USER_AGENTS,
    ERROR_MESSAGES
)
from stealth_manager import create_stealth_manager

logger = logging.getLogger(__name__)


class WebDriverManager:
    """
    Manages Chrome WebDriver instances for LinkedIn post extraction.
    
    Provides methods for browser initialization, configuration, navigation,
    and element interaction with robust error handling and retry logic.
    """
    
    def __init__(self, headless: bool = True, user_agent: Optional[str] = None, use_proxy: bool = False, proxy_list: Optional[List[str]] = None):
        """
        Initialize WebDriver Manager.
        
        Args:
            headless: Whether to run browser in headless mode
            user_agent: Custom user agent string (random if None)
            use_proxy: Whether to use proxy rotation
            proxy_list: List of proxy servers
        """
        self.headless = headless
        self.user_agent = user_agent or self._get_random_user_agent()
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.stealth_manager = create_stealth_manager(use_proxy, proxy_list)
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration for WebDriver operations."""
        # Reduce selenium logging noise
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        
    def _get_random_user_agent(self) -> str:
        """
        Get a random user agent string.
        
        Returns:
            Random user agent string
        """
        return random.choice(USER_AGENTS)
        
    def _create_chrome_options(self) -> ChromeOptions:
        """
        Create Chrome options with optimal configuration for LinkedIn scraping.
        
        Returns:
            Configured ChromeOptions instance
        """
        options = ChromeOptions()
        
        # Basic options
        if self.headless:
            options.add_argument("--headless")
        
        # User agent
        options.add_argument(f"--user-agent={self.user_agent}")
        
        # Performance and privacy options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Faster loading
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-translate")
        options.add_argument("--disable-features=TranslateUI")
        
        # Anti-detection options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Window size
        options.add_argument("--window-size=1920,1080")
        
        # Additional stealth options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Prefs for better performance
        prefs = {
            "profile.default_content_settings.popups": 0,
            "profile.default_content_settings.notifications": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.media_stream_mic": 2,
            "profile.default_content_setting_values.media_stream_camera": 2,
            "profile.default_content_setting_values.geolocation": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        logger.debug(f"Chrome options configured with user agent: {self.user_agent}")
        return options
        
    def initialize_driver(self, retries: int = 3) -> bool:
        """
        Initialize Chrome WebDriver with automatic driver management.
        
        Args:
            retries: Number of retry attempts on failure
            
        Returns:
            True if initialization successful, False otherwise
        """
        for attempt in range(retries):
            try:
                logger.info(f"Initializing Chrome WebDriver (attempt {attempt + 1}/{retries})")
                
                # Get Chrome driver path
                chrome_driver_path = ChromeDriverManager().install()
                logger.debug(f"Chrome driver path: {chrome_driver_path}")
                
                # Create service and options
                service = ChromeService(executable_path=chrome_driver_path)
                options = self._create_chrome_options()
                
                # Configure proxy if available
                options = self.stealth_manager.configure_proxy_for_selenium(options)
                
                # Initialize driver
                self.driver = webdriver.Chrome(service=service, options=options)
                
                # Configure timeouts
                self.driver.implicitly_wait(TIMEOUTS["implicit_wait"])
                self.driver.set_page_load_timeout(TIMEOUTS["page_load_timeout"])
                
                # Initialize WebDriverWait
                self.wait = WebDriverWait(self.driver, TIMEOUTS["explicit_wait"])
                
                # Execute stealth scripts to hide automation
                self._execute_stealth_scripts()
                
                logger.info("Chrome WebDriver initialized successfully")
                return True
                
            except SessionNotCreatedException as e:
                logger.error(f"WebDriver session creation failed: {e}")
                if attempt < retries - 1:
                    logger.info(f"Retrying WebDriver initialization in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                else:
                    logger.error("All WebDriver initialization attempts failed")
                    
            except Exception as e:
                logger.error(f"Unexpected error during WebDriver initialization: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error("WebDriver initialization failed after all retries")
                    
        return False
        
    def navigate_to_url(self, url: str, wait_for_load: bool = True) -> bool:
        """
        Navigate to a specific URL.
        
        Args:
            url: Target URL
            wait_for_load: Whether to wait for page to load
            
        Returns:
            True if navigation successful, False otherwise
        """
        if not self.driver:
            logger.error("WebDriver not initialized")
            return False
            
        try:
            logger.info(f"Navigating to: {url}")
            
            # Apply stealth delay before navigation
            self.stealth_manager.wait_random_delay(2, 5)
            
            self.driver.get(url)
            
            if wait_for_load and self.wait:
                # Wait for page to load
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
            logger.debug(f"Successfully navigated to: {url}")
            return True
            
        except TimeoutException:
            logger.error(f"Timeout while loading page: {url}")
            return False
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return False
            
    def wait_for_element(self, locator: tuple, timeout: Optional[int] = None) -> Optional[Any]:
        """
        Wait for an element to be present and visible.
        
        Args:
            locator: Element locator tuple (By.METHOD, "selector")
            timeout: Custom timeout in seconds
            
        Returns:
            WebElement if found, None otherwise
        """
        if not self.driver:
            logger.error("WebDriver not initialized")
            return None
            
        try:
            if timeout:
                wait = WebDriverWait(self.driver, timeout)
            else:
                wait = self.wait
            
            if not wait:
                logger.error("WebDriverWait not initialized")
                return None
                
            element = wait.until(EC.presence_of_element_located(locator))
            logger.debug(f"Element found: {locator}")
            return element
            
        except TimeoutException:
            logger.debug(f"Element not found within timeout: {locator}")
            return None
        except Exception as e:
            logger.error(f"Error waiting for element {locator}: {e}")
            return None
            
    def wait_for_elements(self, locator: tuple, timeout: Optional[int] = None) -> List[Any]:
        """
        Wait for multiple elements to be present.
        
        Args:
            locator: Element locator tuple (By.METHOD, "selector")
            timeout: Custom timeout in seconds
            
        Returns:
            List of WebElements
        """
        if not self.driver:
            logger.error("WebDriver not initialized")
            return []
            
        try:
            if timeout:
                wait = WebDriverWait(self.driver, timeout)
            else:
                wait = self.wait
            
            if not wait:
                logger.error("WebDriverWait not initialized")
                return []
                
            elements = wait.until(EC.presence_of_all_elements_located(locator))
            logger.debug(f"Found {len(elements)} elements: {locator}")
            return elements
            
        except TimeoutException:
            logger.debug(f"Elements not found within timeout: {locator}")
            return []
        except Exception as e:
            logger.error(f"Error waiting for elements {locator}: {e}")
            return []
            
    def scroll_to_element(self, element: Any) -> bool:
        """
        Scroll to a specific element.
        
        Args:
            element: WebElement to scroll to
            
        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            logger.error("WebDriver not initialized")
            return False
            
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)  # Small delay for smooth scrolling
            return True
        except Exception as e:
            logger.error(f"Error scrolling to element: {e}")
            return False
            
    def scroll_page(self, direction: str = "down", pixels: int = 800) -> bool:
        """
        Scroll the page in the specified direction.
        
        Args:
            direction: "down" or "up"
            pixels: Number of pixels to scroll
            
        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            logger.error("WebDriver not initialized")
            return False
            
        try:
            if direction == "down":
                self.driver.execute_script(f"window.scrollBy(0, {pixels});")
            else:
                self.driver.execute_script(f"window.scrollBy(0, -{pixels});")
            time.sleep(0.5)  # Small delay
            return True
        except Exception as e:
            logger.error(f"Error scrolling page: {e}")
            return False
            
    def get_page_source(self) -> Optional[str]:
        """
        Get the current page source.
        
        Returns:
            Page source HTML or None if error
        """
        if not self.driver:
            logger.error("WebDriver not initialized")
            return None
            
        try:
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Error getting page source: {e}")
            return None
            
    def take_screenshot(self, filename: str) -> bool:
        """
        Take a screenshot of the current page.
        
        Args:
            filename: Screenshot filename
            
        Returns:
            True if successful, False otherwise
        """
        if not self.driver:
            logger.error("WebDriver not initialized")
            return False
            
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return False
            
    def close(self):
        """Close the WebDriver instance."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
                self.wait = None
                
    def __enter__(self):
        """Context manager entry."""
        if not self.initialize_driver():
            raise RuntimeError("Failed to initialize WebDriver")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        
    def is_initialized(self) -> bool:
        """Check if WebDriver is initialized and ready."""
        return self.driver is not None
        
    def get_current_url(self) -> Optional[str]:
        """
        Get the current URL.
        
        Returns:
            Current URL or None if error
        """
        if not self.driver:
            logger.error("WebDriver not initialized")
            return None
            
        try:
            return self.driver.current_url
        except Exception as e:
            logger.error(f"Error getting current URL: {e}")
            return None
        
    def _execute_stealth_scripts(self):
        """
        Execute JavaScript to hide automation indicators and make browser appear more human-like.
        """
        if not self.driver:
            logger.warning("Driver not initialized, skipping stealth scripts")
            return
            
        try:
            # Execute stealth JavaScript code
            stealth_code = self.stealth_manager.get_javascript_stealth_code()
            self.driver.execute_script(stealth_code)
            
            logger.debug("Stealth scripts executed successfully")
            
        except Exception as e:
            logger.warning(f"Failed to execute stealth scripts: {e}")

    def load_cookies(self, cookie_path: Path) -> None:
        """Load cookies from a file into the current browser session."""
        if not self.driver:
            logger.error("WebDriver not initialized, cannot load cookies.")
            return

        if not cookie_path.exists():
            logger.warning(f"Cookie file not found at {cookie_path}, skipping.")
            return

        try:
            with open(cookie_path, 'r') as f:
                cookies = json.load(f)
            
            # For loading cookies, we must first be on the domain.
            # We navigate to the base domain before adding the cookies.
            self.driver.get("https://www.linkedin.com/")
            # Clear any cookies first to avoid conflicts
            self.driver.delete_all_cookies()
            
            accepted_keys = {"name", "value", "domain", "path", "expiry", "httpOnly", "secure", "sameSite"}
            success_count = 0
            for cookie in cookies:
                try:
                    # Keep only accepted keys
                    sanitized = {k: v for k, v in cookie.items() if k in accepted_keys}
                    
                    # Remove attributes that often break Selenium
                    sanitized.pop("sameSite", None)  # Selenium 4.21 still dislikes some sameSite values
                    # Remove expiry if not int
                    if isinstance(sanitized.get("expiry"), str):
                        sanitized.pop("expiry")
                    
                    self.driver.add_cookie(sanitized)
                    success_count += 1
                except Exception as cookie_err:
                    logger.debug(f"Skipping cookie {cookie.get('name')} due to error: {cookie_err}")
            
            logger.info(f"Successfully loaded {success_count}/{len(cookies)} cookies for linkedin.com.")

        except json.JSONDecodeError as jde:
            logger.error(f"Cookie file is not valid JSON: {jde}")
        except Exception as e:
            logger.error(f"An error occurred while loading cookies: {e!r}")

    def get_driver(self) -> webdriver.Chrome:
        """Return the managed WebDriver instance."""
        return self.driver
