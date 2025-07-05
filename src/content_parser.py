"""
LinkedIn Post Extractor - Content Parser Module

This module provides HTML parsing and content extraction functionality for LinkedIn posts.
It uses BeautifulSoup to parse HTML and extract relevant post information including
content, timestamps, author information, and engagement metrics.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from bs4 import BeautifulSoup, Tag
import logging

from config import LINKEDIN_SELECTORS, ERROR_MESSAGES

logger = logging.getLogger(__name__)


@dataclass
class PostData:
    """Data class to represent a LinkedIn post."""
    content: str = ""
    author: str = ""
    timestamp: Optional[datetime] = None
    post_url: str = ""
    engagement_metrics: Dict[str, int] = field(default_factory=dict)
    post_type: str = "text"  # text, image, video, shared_content
    images: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    external_links: List[str] = field(default_factory=list)
    raw_html: str = ""
    
    def __post_init__(self):
        """Post-process the data after initialization."""
        if self.content:
            self.hashtags = self._extract_hashtags(self.content)
            self.mentions = self._extract_mentions(self.content)
            self.external_links = self._extract_external_links(self.content)
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text."""
        hashtag_pattern = r'#[\w\d]+(?:[\w\d\-_]*[\w\d])?'
        return re.findall(hashtag_pattern, text)
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from text."""
        mention_pattern = r'@[\w\d]+(?:[\w\d\-_]*[\w\d])?'
        return re.findall(mention_pattern, text)
    
    def _extract_external_links(self, text: str) -> List[str]:
        """Extract external links from text."""
        url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+\.[^\s<>"\']*'
        return re.findall(url_pattern, text)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert PostData to dictionary."""
        return {
            'content': self.content,
            'author': self.author,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'post_url': self.post_url,
            'engagement_metrics': self.engagement_metrics,
            'post_type': self.post_type,
            'images': self.images,
            'hashtags': self.hashtags,
            'mentions': self.mentions,
            'external_links': self.external_links,
            'raw_html': self.raw_html
        }


class LinkedInContentParser:
    """
    Parser for LinkedIn HTML content to extract post information.
    
    This class handles the parsing of LinkedIn profile pages and extraction
    of post content, metadata, and engagement information.
    """
    
    def __init__(self):
        """Initialize the content parser."""
        self.selectors = LINKEDIN_SELECTORS
        self.stats = {
            'total_posts_found': 0,
            'successfully_parsed': 0,
            'failed_to_parse': 0,
            'empty_posts': 0
        }
    
    def parse_profile_page(self, html_content: str) -> List[PostData]:
        """
        Parse a LinkedIn profile page and extract all posts.
        
        Args:
            html_content: HTML content of the LinkedIn profile page
            
        Returns:
            List of PostData objects representing the posts
        """
        if not html_content:
            logger.error("Empty HTML content provided")
            return []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            posts = []
            
            # Find all post containers
            post_containers = self._find_post_containers(soup)
            self.stats['total_posts_found'] = len(post_containers)
            
            logger.info(f"Found {len(post_containers)} potential post containers")
            
            for i, container in enumerate(post_containers):
                try:
                    post_data = self._parse_post_container(container)
                    if post_data and post_data.content.strip():
                        posts.append(post_data)
                        self.stats['successfully_parsed'] += 1
                        logger.debug(f"Successfully parsed post {i+1}")
                    else:
                        self.stats['empty_posts'] += 1
                        logger.debug(f"Post {i+1} is empty or invalid")
                        
                except Exception as e:
                    self.stats['failed_to_parse'] += 1
                    logger.error(f"Failed to parse post {i+1}: {e}")
                    
            logger.info(f"Successfully parsed {len(posts)} posts out of {len(post_containers)} containers")
            return posts
            
        except Exception as e:
            logger.error(f"Failed to parse profile page: {e}")
            return []
    
    def _find_post_containers(self, soup: BeautifulSoup) -> List[Tag]:
        """
        Find all post container elements in the HTML.
        
        Args:
            soup: BeautifulSoup object of the HTML content
            
        Returns:
            List of HTML elements representing post containers
        """
        containers = []
        
        # Try each selector for post containers
        for selector in self.selectors.get('post_container', []):
            try:
                found_containers = soup.select(selector)
                if found_containers:
                    containers.extend(found_containers)
                    logger.debug(f"Found {len(found_containers)} containers with selector: {selector}")
            except Exception as e:
                logger.debug(f"Selector failed: {selector}, error: {e}")
        
        # Remove duplicates while preserving order
        unique_containers = []
        seen = set()
        for container in containers:
            container_id = id(container)
            if container_id not in seen:
                seen.add(container_id)
                unique_containers.append(container)
        
        return unique_containers
    
    def _parse_post_container(self, container: Tag) -> Optional[PostData]:
        """
        Parse a single post container element.
        
        Args:
            container: HTML element representing a post container
            
        Returns:
            PostData object or None if parsing failed
        """
        try:
            post_data = PostData()
            
            # Extract post content
            post_data.content = self._extract_post_content(container)
            
            # Extract author information
            post_data.author = self._extract_author_info(container)
            
            # Extract timestamp
            post_data.timestamp = self._extract_timestamp(container)
            
            # Extract post URL
            post_data.post_url = self._extract_post_url(container)
            
            # Extract engagement metrics
            post_data.engagement_metrics = self._extract_engagement_metrics(container)
            
            # Determine post type
            post_data.post_type = self._determine_post_type(container)
            
            # Extract images
            post_data.images = self._extract_images(container)
            
            # Store raw HTML for debugging
            post_data.raw_html = str(container)
            
            return post_data
            
        except Exception as e:
            logger.error(f"Failed to parse post container: {e}")
            return None
    
    def _extract_post_content(self, container: Tag) -> str:
        """
        Extract the main content/text of a post.
        
        Args:
            container: HTML element representing a post container
            
        Returns:
            Cleaned post content text
        """
        content = ""
        
        # Try different selectors for post content
        for selector in self.selectors.get('post_content', []):
            try:
                content_elements = container.select(selector)
                if content_elements:
                    # Get text from all matching elements
                    content_parts = []
                    for element in content_elements:
                        text = element.get_text(strip=True)
                        if text:
                            content_parts.append(text)
                    
                    if content_parts:
                        content = ' '.join(content_parts)
                        break
                        
            except Exception as e:
                logger.debug(f"Content selector failed: {selector}, error: {e}")
        
        # Clean up content
        content = self._clean_text(content)
        
        logger.debug(f"Extracted content: {content[:100]}...")
        return content
    
    def _extract_author_info(self, container: Tag) -> str:
        """
        Extract author information from a post.
        
        Args:
            container: HTML element representing a post container
            
        Returns:
            Author name or empty string if not found
        """
        author = ""
        
        # Try different selectors for author name
        for selector in self.selectors.get('author_name', []):
            try:
                author_elements = container.select(selector)
                if author_elements:
                    author = author_elements[0].get_text(strip=True)
                    if author:
                        break
                        
            except Exception as e:
                logger.debug(f"Author selector failed: {selector}, error: {e}")
        
        logger.debug(f"Extracted author: {author}")
        return author
    
    def _extract_timestamp(self, container: Tag) -> Optional[datetime]:
        """
        Extract timestamp from a post.
        
        Args:
            container: HTML element representing a post container
            
        Returns:
            datetime object or None if not found
        """
        timestamp = None
        
        # Try different selectors for timestamp
        for selector in self.selectors.get('post_date', []):
            try:
                time_elements = container.select(selector)
                if time_elements:
                    time_element = time_elements[0]
                    
                    # Try to get datetime attribute
                    datetime_attr = time_element.get('datetime')
                    if datetime_attr:
                        timestamp = self._parse_datetime_string(datetime_attr)
                        if timestamp:
                            break
                    
                    # Try to parse text content
                    time_text = time_element.get_text(strip=True)
                    if time_text:
                        timestamp = self._parse_time_text(time_text)
                        if timestamp:
                            break
                            
            except Exception as e:
                logger.debug(f"Timestamp selector failed: {selector}, error: {e}")
        
        logger.debug(f"Extracted timestamp: {timestamp}")
        return timestamp
    
    def _extract_post_url(self, container: Tag) -> str:
        """
        Extract post URL from a post container.
        
        Args:
            container: HTML element representing a post container
            
        Returns:
            Post URL or empty string if not found
        """
        post_url = ""
        
        # Try to find link elements
        link_elements = container.find_all('a', href=True)
        for link in link_elements:
            href = link.get('href', '')
            if 'linkedin.com' in href and 'activity' in href:
                post_url = href
                break
        
        logger.debug(f"Extracted post URL: {post_url}")
        return post_url
    
    def _extract_engagement_metrics(self, container: Tag) -> Dict[str, int]:
        """
        Extract engagement metrics (likes, comments, shares) from a post.
        
        Args:
            container: HTML element representing a post container
            
        Returns:
            Dictionary with engagement metrics
        """
        metrics = {
            'likes': 0,
            'comments': 0,
            'shares': 0,
            'reactions': 0
        }
        
        # Try to find engagement elements
        # This is a simplified implementation as LinkedIn's engagement selectors
        # can be complex and change frequently
        try:
            # Look for like counts
            like_elements = container.find_all(['span', 'button'], 
                                             string=re.compile(r'\d+.*like', re.IGNORECASE))
            if like_elements:
                like_text = like_elements[0].get_text(strip=True)
                likes = self._extract_number_from_text(like_text)
                if likes:
                    metrics['likes'] = likes
            
            # Look for comment counts
            comment_elements = container.find_all(['span', 'button'], 
                                                 string=re.compile(r'\d+.*comment', re.IGNORECASE))
            if comment_elements:
                comment_text = comment_elements[0].get_text(strip=True)
                comments = self._extract_number_from_text(comment_text)
                if comments:
                    metrics['comments'] = comments
                    
        except Exception as e:
            logger.debug(f"Failed to extract engagement metrics: {e}")
        
        logger.debug(f"Extracted engagement metrics: {metrics}")
        return metrics
    
    def _determine_post_type(self, container: Tag) -> str:
        """
        Determine the type of post (text, image, video, shared_content).
        
        Args:
            container: HTML element representing a post container
            
        Returns:
            Post type string
        """
        post_type = "text"
        
        # Look for images
        if container.find_all('img'):
            post_type = "image"
        
        # Look for videos
        if container.find_all('video') or container.find_all(class_=re.compile(r'video', re.IGNORECASE)):
            post_type = "video"
        
        # Look for shared content
        if container.find_all(class_=re.compile(r'share|shared', re.IGNORECASE)):
            post_type = "shared_content"
        
        logger.debug(f"Determined post type: {post_type}")
        return post_type
    
    def _extract_images(self, container: Tag) -> List[str]:
        """
        Extract image URLs from a post.
        
        Args:
            container: HTML element representing a post container
            
        Returns:
            List of image URLs
        """
        images = []
        
        # Find all img elements
        img_elements = container.find_all('img')
        for img in img_elements:
            src = img.get('src', '')
            if src and src.startswith('http'):
                images.append(src)
        
        logger.debug(f"Extracted {len(images)} images")
        return images
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common LinkedIn UI text
        ui_text_patterns = [
            r'See more$',
            r'Show more$',
            r'…see more$',
            r'Like this post$',
            r'Comment on this post$',
            r'Share this post$',
        ]
        
        for pattern in ui_text_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _parse_datetime_string(self, datetime_str: str) -> Optional[datetime]:
        """
        Parse a datetime string into a datetime object.
        
        Args:
            datetime_str: String representation of datetime
            
        Returns:
            datetime object or None if parsing failed
        """
        try:
            # Try common datetime formats
            formats = [
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(datetime_str, fmt)
                except ValueError:
                    continue
                    
        except Exception as e:
            logger.debug(f"Failed to parse datetime string '{datetime_str}': {e}")
        
        return None
    
    def _parse_time_text(self, time_text: str) -> Optional[datetime]:
        """
        Parse time text like '2 hours ago', 'Yesterday', etc.
        
        Args:
            time_text: Human-readable time text
            
        Returns:
            datetime object or None if parsing failed
        """
        try:
            # This is a simplified implementation
            # In a real application, you'd want more sophisticated parsing
            now = datetime.now()
            
            if 'hour' in time_text.lower():
                # Extract hours
                hours = self._extract_number_from_text(time_text)
                if hours:
                    return now - timedelta(hours=hours)
            
            if 'day' in time_text.lower():
                # Extract days
                days = self._extract_number_from_text(time_text)
                if days:
                    return now - timedelta(days=days)
            
            if 'week' in time_text.lower():
                # Extract weeks
                weeks = self._extract_number_from_text(time_text)
                if weeks:
                    return now - timedelta(weeks=weeks)
                    
        except Exception as e:
            logger.debug(f"Failed to parse time text '{time_text}': {e}")
        
        return None
    
    def _extract_number_from_text(self, text: str) -> Optional[int]:
        """
        Extract a number from text.
        
        Args:
            text: Text containing a number
            
        Returns:
            Extracted number or None if not found
        """
        try:
            # Look for numbers in the text
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])
        except Exception as e:
            logger.debug(f"Failed to extract number from text '{text}': {e}")
        
        return None
    
    def get_parsing_stats(self) -> Dict[str, int]:
        """
        Get parsing statistics.
        
        Returns:
            Dictionary with parsing statistics
        """
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset parsing statistics."""
        self.stats = {
            'total_posts_found': 0,
            'successfully_parsed': 0,
            'failed_to_parse': 0,
            'empty_posts': 0
        }


def parse_linkedin_profile(html_content: str) -> List[PostData]:
    """
    Convenience function to parse LinkedIn profile HTML content.
    
    Args:
        html_content: HTML content of the LinkedIn profile page
        
    Returns:
        List of PostData objects
    """
    parser = LinkedInContentParser()
    return parser.parse_profile_page(html_content)


def extract_post_summary(posts: List[PostData]) -> Dict[str, Any]:
    """
    Extract summary information from a list of posts.
    
    Args:
        posts: List of PostData objects
        
    Returns:
        Dictionary with summary information
    """
    if not posts:
        return {'total_posts': 0, 'summary': 'No posts found'}
    
    total_posts = len(posts)
    post_types = {}
    hashtags = set()
    authors = set()
    
    for post in posts:
        # Count post types
        post_types[post.post_type] = post_types.get(post.post_type, 0) + 1
        
        # Collect hashtags
        hashtags.update(post.hashtags)
        
        # Collect authors
        if post.author:
            authors.add(post.author)
    
    return {
        'total_posts': total_posts,
        'post_types': post_types,
        'unique_hashtags': len(hashtags),
        'common_hashtags': list(hashtags)[:10],  # Top 10 hashtags
        'unique_authors': len(authors),
        'authors': list(authors)
    }
