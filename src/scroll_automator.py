"""
LinkedIn Post Extractor - Scroll Automation Module

This module provides infinite scroll automation functionality to handle LinkedIn's
dynamically loaded content. It includes JavaScript-based scrolling, content
detection, and loop prevention mechanisms.
"""

import time
import logging
import random
from typing import Dict, List, Optional, Tuple, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)


class ScrollAutomator:
    """
    Handles infinite scroll automation for LinkedIn profile pages.
    
    This class provides JavaScript-based scrolling capabilities with content
    detection, loop prevention, and configurable delays for dynamic content loading.
    """
    
    def __init__(self, driver, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the scroll automator.
        
        Args:
            driver: Selenium WebDriver instance
            config: Configuration dictionary with scroll settings
        """
        self.driver = driver
        self.config = config or self._get_default_config()
        self.scroll_history = []
        self.content_hashes = set()
        self.stats = {
            'total_scrolls': 0,
            'content_loads': 0,
            'duplicates_detected': 0,
            'timeouts': 0,
            'errors': 0,
            'retries': 0,
            'backoff_delays': 0
        }
        
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration for scroll automation.
        
        Returns:
            Default configuration dictionary
        """
        return {
            'scroll_pause_time': 2.0,  # Seconds to wait after each scroll
            'max_scrolls': 50,  # Maximum number of scroll attempts
            'scroll_step': 800,  # Pixels to scroll per step
            'content_wait_timeout': 10,  # Seconds to wait for content to load
            'no_new_content_threshold': 3,  # Number of consecutive scrolls with no new content
            'duplicate_detection': True,  # Enable duplicate content detection
            'debug_mode': False,  # Enable debug logging
            'max_retries': 3,  # Maximum number of retry attempts for failed operations
            'retry_backoff_base': 1.0,  # Base delay for exponential backoff (seconds)
            'retry_backoff_multiplier': 2.0,  # Multiplier for exponential backoff
            'random_delay_variation': 0.5,  # Random variation in delays (0-1)
            'human_like_scrolling': True  # Enable human-like scrolling behavior
        }
    
    def scroll_to_load_all_content(self) -> Dict[str, Any]:
        """
        Perform infinite scroll to load all available content.
        
        Returns:
            Dictionary with scroll results and statistics
        """
        logger.info("Starting infinite scroll automation")
        
        # Reset statistics
        self.stats = {key: 0 for key in self.stats}
        
        try:
            # Initial page height check
            initial_height = self._get_page_height()
            logger.debug(f"Initial page height: {initial_height}px")
            
            consecutive_no_new_content = 0
            last_content_hash = None
            
            for scroll_count in range(self.config['max_scrolls']):
                self.stats['total_scrolls'] = scroll_count + 1
                
                # Perform scroll action with retry logic
                scroll_result = self._perform_scroll_with_retry()
                if not scroll_result['success']:
                    logger.warning(f"Scroll {scroll_count + 1} failed: {scroll_result['error']}")
                    self.stats['errors'] += 1
                    if self.stats['errors'] > 3:
                        logger.error("Too many scroll errors, stopping automation")
                        break
                    continue
                
                # Wait for content to load with retry
                self._wait_for_content_with_retry()
                
                # Check for new content
                current_content_hash = self._get_content_hash()
                if current_content_hash == last_content_hash:
                    consecutive_no_new_content += 1
                    logger.debug(f"No new content detected (consecutive: {consecutive_no_new_content})")
                else:
                    consecutive_no_new_content = 0
                    last_content_hash = current_content_hash
                    self.stats['content_loads'] += 1
                    logger.debug(f"New content detected after scroll {scroll_count + 1}")
                
                # Check if we should stop scrolling
                if self._should_stop_scrolling(consecutive_no_new_content):
                    logger.info(f"Stopping scroll automation after {scroll_count + 1} scrolls")
                    break
                
                # Pause between scrolls with human-like variation
                pause_time = self._get_human_like_delay(self.config['scroll_pause_time'])
                time.sleep(pause_time)
            
            # Final statistics
            final_height = self._get_page_height()
            logger.info(f"Scroll automation completed: {self.stats['total_scrolls']} scrolls, "
                       f"page height: {initial_height}px → {final_height}px")
            
            return {
                'success': True,
                'stats': self.stats.copy(),
                'initial_height': initial_height,
                'final_height': final_height,
                'content_loaded': self.stats['content_loads'] > 0
            }
            
        except Exception as e:
            logger.error(f"Scroll automation failed: {e}", exc_info=True)
            self.stats['errors'] += 1
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats.copy()
            }
    
    def _perform_scroll(self) -> Dict[str, Any]:
        """
        Perform a single scroll action using JavaScript.
        
        Returns:
            Dictionary with scroll result
        """
        try:
            # Get current scroll position
            current_position = self._get_scroll_position()
            
            # Execute JavaScript scroll
            scroll_script = f"""
                window.scrollBy({{
                    top: {self.config['scroll_step']},
                    left: 0,
                    behavior: 'smooth'
                }});
                return {{
                    scrollTop: window.pageYOffset || document.documentElement.scrollTop,
                    scrollHeight: document.documentElement.scrollHeight,
                    clientHeight: window.innerHeight
                }};
            """
            
            result = self.driver.execute_script(scroll_script)
            
            # Record scroll position
            new_position = result['scrollTop']
            self.scroll_history.append({
                'position': new_position,
                'timestamp': time.time(),
                'scroll_height': result['scrollHeight']
            })
            
            # Check if scroll was effective
            if new_position <= current_position:
                return {
                    'success': False,
                    'error': 'No scroll movement detected (reached bottom?)',
                    'position': new_position
                }
            
            if self.config['debug_mode']:
                logger.debug(f"Scrolled to position {new_position}px "
                           f"(page height: {result['scrollHeight']}px)")
            
            return {
                'success': True,
                'position': new_position,
                'scroll_height': result['scrollHeight'],
                'client_height': result['clientHeight']
            }
            
        except WebDriverException as e:
            return {
                'success': False,
                'error': f'WebDriver error during scroll: {e}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error during scroll: {e}'
            }
    
    def _wait_for_content_load(self):
        """
        Wait for new content to load after scrolling.
        
        Uses various strategies to detect when content has finished loading.
        """
        try:
            # Strategy 1: Wait for potential loading indicators to disappear
            self._wait_for_loading_indicators()
            
            # Strategy 2: Wait for network activity to settle
            time.sleep(0.5)  # Brief pause for network requests
            
            # Strategy 3: Wait for DOM to stabilize
            self._wait_for_dom_stability()
            
        except TimeoutException:
            self.stats['timeouts'] += 1
            logger.debug("Timeout waiting for content to load")
        except Exception as e:
            logger.debug(f"Error waiting for content load: {e}")
    
    def _wait_for_loading_indicators(self):
        """
        Wait for common LinkedIn loading indicators to disappear.
        """
        loading_selectors = [
            '[data-test-id="loading-indicator"]',
            '.artdeco-spinner',
            '.feed-shared-update-v2__skeleton',
            '[aria-label*="Loading"]'
        ]
        
        for selector in loading_selectors:
            try:
                # Wait for loading indicator to appear and then disappear
                WebDriverWait(self.driver, 1).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
                )
            except TimeoutException:
                # Loading indicator not found or already gone
                continue
    
    def _wait_for_dom_stability(self):
        """
        Wait for DOM to stabilize (no new elements being added).
        """
        try:
            # Check DOM stability by comparing element counts
            stability_script = """
                var initialCount = document.querySelectorAll('*').length;
                var stabilityTimeout = setTimeout(function() {
                    window.domStabilityCheck = {
                        stable: true,
                        initialCount: initialCount,
                        finalCount: document.querySelectorAll('*').length
                    };
                }, 500);
                return initialCount;
            """
            
            initial_count = self.driver.execute_script(stability_script)
            
            # Wait and check if DOM is stable
            time.sleep(0.6)
            
            stability_check = self.driver.execute_script("""
                return window.domStabilityCheck || {stable: false};
            """)
            
            if self.config['debug_mode'] and stability_check.get('stable'):
                logger.debug(f"DOM stability check: {stability_check}")
                
        except Exception as e:
            logger.debug(f"DOM stability check failed: {e}")
    
    def _get_content_hash(self) -> str:
        """
        Generate a hash of current visible content for duplicate detection.
        
        Returns:
            Hash string representing current content
        """
        if not self.config['duplicate_detection']:
            return str(time.time())  # Return timestamp if duplicate detection disabled
        
        try:
            # Get text content of main post containers
            content_script = """
                var posts = document.querySelectorAll('[data-id], .feed-shared-update-v2');
                var contentArray = [];
                posts.forEach(function(post, index) {
                    var textContent = post.textContent || '';
                    if (textContent.trim().length > 10) {  // Filter out empty/short content
                        contentArray.push(textContent.trim().substring(0, 100));  // First 100 chars
                    }
                });
                return contentArray.join('|');
            """
            
            content_text = self.driver.execute_script(content_script)
            content_hash = str(hash(content_text))
            
            # Track for duplicate detection
            if content_hash in self.content_hashes:
                self.stats['duplicates_detected'] += 1
            else:
                self.content_hashes.add(content_hash)
            
            return content_hash
            
        except Exception as e:
            logger.debug(f"Content hash generation failed: {e}")
            return str(time.time())
    
    def _should_stop_scrolling(self, consecutive_no_new_content: int) -> bool:
        """
        Determine if scrolling should stop based on various conditions.
        
        Args:
            consecutive_no_new_content: Number of consecutive scrolls with no new content
            
        Returns:
            True if scrolling should stop
        """
        # Stop if no new content for several scrolls
        if consecutive_no_new_content >= self.config['no_new_content_threshold']:
            logger.info(f"Stopping: No new content for {consecutive_no_new_content} consecutive scrolls")
            return True
        
        # Stop if we've reached the absolute bottom
        if self._is_at_bottom():
            logger.info("Stopping: Reached bottom of page")
            return True
        
        # Stop if too many errors
        if self.stats['errors'] > 5:
            logger.warning("Stopping: Too many scroll errors")
            return True
        
        return False
    
    def _is_at_bottom(self) -> bool:
        """
        Check if we've reached the bottom of the page.
        
        Returns:
            True if at bottom of page
        """
        try:
            bottom_check_script = """
                var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                var scrollHeight = document.documentElement.scrollHeight;
                var clientHeight = window.innerHeight;
                return (scrollTop + clientHeight) >= (scrollHeight - 50);  // 50px tolerance
            """
            
            return self.driver.execute_script(bottom_check_script)
            
        except Exception as e:
            logger.debug(f"Bottom check failed: {e}")
            return False
    
    def _get_scroll_position(self) -> int:
        """
        Get current scroll position.
        
        Returns:
            Current scroll position in pixels
        """
        try:
            return self.driver.execute_script(
                "return window.pageYOffset || document.documentElement.scrollTop;"
            )
        except Exception:
            return 0
    
    def _get_page_height(self) -> int:
        """
        Get total page height.
        
        Returns:
            Page height in pixels
        """
        try:
            return self.driver.execute_script(
                "return document.documentElement.scrollHeight;"
            )
        except Exception:
            return 0
    
    def get_scroll_stats(self) -> Dict[str, Any]:
        """
        Get scrolling statistics.
        
        Returns:
            Dictionary with scroll statistics
        """
        return {
            'stats': self.stats.copy(),
            'config': self.config.copy(),
            'scroll_history_length': len(self.scroll_history),
            'content_hashes_tracked': len(self.content_hashes)
        }
    
    def reset_state(self):
        """Reset scroll automation state."""
        self.scroll_history.clear()
        self.content_hashes.clear()
        self.stats = {key: 0 for key in self.stats}
        logger.debug("Scroll automation state reset")
    
    def _execute_with_retry(self, operation, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute an operation with retry logic and exponential backoff.
        
        Args:
            operation: Function to execute
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Dictionary with operation result
        """
        max_retries = self.config['max_retries']
        base_delay = self.config['retry_backoff_base']
        multiplier = self.config['retry_backoff_multiplier']
        
        for attempt in range(max_retries + 1):
            try:
                result = operation(*args, **kwargs)
                if attempt > 0:
                    logger.debug(f"Operation succeeded on attempt {attempt + 1}")
                return result if isinstance(result, dict) else {'success': True, 'result': result}
                
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"Operation failed after {max_retries + 1} attempts: {e}")
                    self.stats['errors'] += 1
                    return {
                        'success': False,
                        'error': f'Failed after {max_retries + 1} attempts: {e}',
                        'attempts': attempt + 1
                    }
                
                # Calculate backoff delay with exponential backoff
                delay = base_delay * (multiplier ** attempt)
                
                # Add random variation to avoid thundering herd
                if self.config['random_delay_variation'] > 0:
                    variation = random.uniform(0, self.config['random_delay_variation'])
                    delay += delay * variation
                
                logger.debug(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s")
                self.stats['retries'] += 1
                self.stats['backoff_delays'] += 1
                
                time.sleep(delay)
        
        # This should never be reached, but adding for safety
        return {
            'success': False,
            'error': 'Unexpected end of retry loop',
            'attempts': max_retries + 1
        }
    
    def _get_human_like_delay(self, base_delay: float) -> float:
        """
        Calculate human-like delay with random variation.
        
        Args:
            base_delay: Base delay in seconds
            
        Returns:
            Adjusted delay with human-like variation
        """
        if not self.config['human_like_scrolling']:
            return base_delay
        
        # Add random variation (±20% of base delay)
        variation = random.uniform(-0.2, 0.2)
        adjusted_delay = base_delay * (1 + variation)
        
        # Ensure minimum delay
        return max(adjusted_delay, 0.5)
    
    def _perform_scroll_with_retry(self) -> Dict[str, Any]:
        """
        Perform scroll operation with retry logic.
        
        Returns:
            Dictionary with scroll result
        """
        return self._execute_with_retry(self._perform_scroll)
    
    def _wait_for_content_with_retry(self):
        """
        Wait for content to load with retry logic.
        """
        def wait_operation():
            self._wait_for_content_load()
            return {'success': True}
        
        result = self._execute_with_retry(wait_operation)
        if not result.get('success', False):
            logger.warning("Content loading wait failed after retries")


def create_scroll_automator(driver, **config_overrides) -> ScrollAutomator:
    """
    Create a ScrollAutomator instance with optional configuration overrides.
    
    Args:
        driver: Selenium WebDriver instance
        **config_overrides: Configuration values to override defaults
        
    Returns:
        Configured ScrollAutomator instance
    """
    automator = ScrollAutomator(driver)
    
    # Apply configuration overrides
    if config_overrides:
        automator.config.update(config_overrides)
        logger.debug(f"Applied config overrides: {config_overrides}")
    
    return automator
