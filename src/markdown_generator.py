"""
LinkedIn Post Extractor - Markdown Generator Module

This module provides functionality to convert extracted LinkedIn posts into
well-formatted Markdown files with metadata, proper structure, and readable layout.
"""

import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from content_parser import PostData
from config import OUTPUT_CONFIG, MARKDOWN_TEMPLATE

logger = logging.getLogger(__name__)


class MarkdownGenerator:
    """
    Generator for creating Markdown files from LinkedIn post data.
    
    This class handles the conversion of PostData objects into structured Markdown
    format with YAML frontmatter, proper formatting, and metadata preservation.
    """
    
    def __init__(self, output_dir: str = "."):
        """
        Initialize the Markdown generator.
        
        Args:
            output_dir: Directory where Markdown files will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {
            'files_created': 0,
            'posts_processed': 0,
            'errors': 0
        }
        
    def generate_markdown_file(
        self, 
        posts: List[PostData], 
        profile_name: str,
        profile_url: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a Markdown file from a list of posts.
        
        Args:
            posts: List of PostData objects to convert
            profile_name: Name of the LinkedIn profile
            profile_url: URL of the LinkedIn profile
            filename: Custom filename (optional)
            
        Returns:
            Path to the generated Markdown file
        """
        try:
            # Generate filename if not provided
            if not filename:
                filename = self._generate_filename(profile_name)
            
            # Ensure .md extension
            if not filename.endswith('.md'):
                filename += '.md'
            
            file_path = self.output_dir / filename
            
            # Generate Markdown content
            markdown_content = self._generate_markdown_content(
                posts, profile_name, profile_url
            )
            
            # Write to file
            with open(file_path, 'w', encoding=OUTPUT_CONFIG['encoding']) as f:
                f.write(markdown_content)
            
            self.stats['files_created'] += 1
            self.stats['posts_processed'] += len(posts)
            
            logger.info(f"Generated Markdown file: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Failed to generate Markdown file: {e}")
            raise
    
    def _generate_filename(self, profile_name: str) -> str:
        """
        Generate a filename based on profile name and current date.
        
        Args:
            profile_name: Name of the LinkedIn profile
            
        Returns:
            Generated filename
        """
        # Clean profile name for filename
        clean_name = self._sanitize_filename(profile_name)
        
        # Add current date
        current_date = datetime.now().strftime(OUTPUT_CONFIG['date_format'])
        
        # Use template
        filename = OUTPUT_CONFIG['filename_template'].format(
            profile_name=clean_name,
            date=current_date
        )
        
        # Ensure filename length is reasonable
        max_length = OUTPUT_CONFIG['max_filename_length']
        if len(filename) > max_length:
            # Truncate profile name part
            name_part = clean_name
            extension = '.md'
            date_part = f'-posts-{current_date}'
            
            max_name_length = max_length - len(date_part) - len(extension)
            if max_name_length > 0:
                name_part = name_part[:max_name_length]
                filename = f"{name_part}{date_part}{extension}"
            else:
                filename = f"posts-{current_date}{extension}"
        
        return filename
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a string to be safe for use as a filename.
        
        Args:
            filename: Raw filename string
            
        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, '-', filename)
        
        # Remove multiple consecutive dashes
        sanitized = re.sub(r'-+', '-', sanitized)
        
        # Remove leading/trailing dashes and spaces
        sanitized = sanitized.strip('- ')
        
        # Fallback if empty
        if not sanitized:
            sanitized = "linkedin-profile"
        
        return sanitized
    
    def _generate_markdown_content(
        self, 
        posts: List[PostData], 
        profile_name: str,
        profile_url: str
    ) -> str:
        """
        Generate the complete Markdown content.
        
        Args:
            posts: List of PostData objects
            profile_name: Name of the LinkedIn profile
            profile_url: URL of the LinkedIn profile
            
        Returns:
            Complete Markdown content as string
        """
        # Start with YAML frontmatter
        frontmatter = self._generate_frontmatter(posts, profile_name, profile_url)
        
        # Generate header
        header = self._generate_header(posts, profile_name, profile_url)
        
        # Generate posts content
        posts_content = self._generate_posts_content(posts)
        
        # Generate footer
        footer = self._generate_footer(posts)
        
        # Combine all parts
        content_parts = [
            frontmatter,
            header,
            posts_content,
            footer
        ]
        
        return '\n'.join(filter(None, content_parts))
    
    def _generate_frontmatter(
        self, 
        posts: List[PostData], 
        profile_name: str,
        profile_url: str
    ) -> str:
        """
        Generate YAML frontmatter for the Markdown file.
        
        Args:
            posts: List of PostData objects
            profile_name: Name of the LinkedIn profile
            profile_url: URL of the LinkedIn profile
            
        Returns:
            YAML frontmatter as string
        """
        extraction_date = datetime.now().isoformat()
        
        # Extract metadata from posts
        post_types = {}
        hashtags = set()
        authors = set()
        date_range = {'earliest': None, 'latest': None}
        
        for post in posts:
            # Count post types
            post_types[post.post_type] = post_types.get(post.post_type, 0) + 1
            
            # Collect hashtags
            hashtags.update(post.hashtags)
            
            # Collect authors
            if post.author:
                authors.add(post.author)
            
            # Track date range
            if post.timestamp:
                if date_range['earliest'] is None or post.timestamp < date_range['earliest']:
                    date_range['earliest'] = post.timestamp
                if date_range['latest'] is None or post.timestamp > date_range['latest']:
                    date_range['latest'] = post.timestamp
        
        frontmatter = f"""---
title: "LinkedIn Posts - {profile_name}"
profile_name: "{profile_name}"
profile_url: "{profile_url}"
extraction_date: "{extraction_date}"
total_posts: {len(posts)}
post_types: {dict(post_types)}
unique_hashtags: {len(hashtags)}
top_hashtags: {list(hashtags)[:10]}
unique_authors: {len(authors)}
date_range:
  earliest: "{date_range['earliest'].isoformat() if date_range['earliest'] else None}"
  latest: "{date_range['latest'].isoformat() if date_range['latest'] else None}"
generated_by: "LinkedIn Post Extractor"
---

"""
        return frontmatter
    
    def _generate_header(
        self, 
        posts: List[PostData], 
        profile_name: str,
        profile_url: str
    ) -> str:
        """
        Generate the header section of the Markdown file.
        
        Args:
            posts: List of PostData objects
            profile_name: Name of the LinkedIn profile
            profile_url: URL of the LinkedIn profile
            
        Returns:
            Header content as string
        """
        extraction_date = datetime.now().strftime("%B %d, %Y at %H:%M")
        
        header = MARKDOWN_TEMPLATE['header'].format(
            profile_name=profile_name,
            extraction_date=extraction_date,
            profile_url=profile_url,
            total_posts=len(posts)
        )
        
        # Add summary statistics
        summary_stats = self._generate_summary_stats(posts)
        header += summary_stats
        
        return header
    
    def _generate_summary_stats(self, posts: List[PostData]) -> str:
        """
        Generate summary statistics section.
        
        Args:
            posts: List of PostData objects
            
        Returns:
            Summary statistics as string
        """
        if not posts:
            return ""
        
        # Calculate statistics
        post_types = {}
        total_engagement = {'likes': 0, 'comments': 0, 'shares': 0}
        hashtags = set()
        
        for post in posts:
            post_types[post.post_type] = post_types.get(post.post_type, 0) + 1
            hashtags.update(post.hashtags)
            
            for metric, value in post.engagement_metrics.items():
                if metric in total_engagement:
                    total_engagement[metric] += value
        
        stats = "## 📊 Summary Statistics\n\n"
        
        if post_types:
            stats += "### Post Types\n"
            for post_type, count in post_types.items():
                percentage = (count / len(posts)) * 100
                stats += f"- **{post_type.replace('_', ' ').title()}**: {count} ({percentage:.1f}%)\n"
            stats += "\n"
        
        if any(total_engagement.values()):
            stats += "### Total Engagement\n"
            for metric, value in total_engagement.items():
                if value > 0:
                    stats += f"- **{metric.title()}**: {value:,}\n"
            stats += "\n"
        
        if hashtags:
            top_hashtags = list(hashtags)[:10]
            stats += f"### Top Hashtags ({len(hashtags)} unique)\n"
            for hashtag in top_hashtags:
                stats += f"- {hashtag}\n"
            stats += "\n"
        
        stats += "---\n\n"
        return stats
    
    def _generate_posts_content(self, posts: List[PostData]) -> str:
        """
        Generate the posts content section.
        
        Args:
            posts: List of PostData objects
            
        Returns:
            Posts content as string
        """
        if not posts:
            return MARKDOWN_TEMPLATE['empty_profile_template'].format(
                profile_name="Profile",
                extraction_date=datetime.now().strftime("%B %d, %Y"),
                profile_url=""
            )
        
        content = "## 📝 Posts\n\n"
        
        for i, post in enumerate(posts, 1):
            post_content = self._format_post(post, i)
            content += post_content + "\n"
        
        return content
    
    def _format_post(self, post: PostData, post_number: int) -> str:
        """
        Format a single post as Markdown.
        
        Args:
            post: PostData object
            post_number: Sequential post number
            
        Returns:
            Formatted post as string
        """
        # Format timestamp
        if post.timestamp:
            post_date = post.timestamp.strftime("%B %d, %Y at %H:%M")
        else:
            post_date = "Date not available"
        
        # Escape Markdown special characters in content
        escaped_content = self._escape_markdown(post.content)
        
        # Build post content
        post_md = f"### Post #{post_number}\n\n"
        
        # Add metadata
        metadata = []
        if post.author:
            metadata.append(f"**Author**: {post.author}")
        metadata.append(f"**Date**: {post_date}")
        metadata.append(f"**Type**: {post.post_type.replace('_', ' ').title()}")
        
        if post.engagement_metrics:
            engagement_parts = []
            for metric, value in post.engagement_metrics.items():
                if value > 0:
                    engagement_parts.append(f"{metric}: {value:,}")
            if engagement_parts:
                metadata.append(f"**Engagement**: {', '.join(engagement_parts)}")
        
        if metadata:
            post_md += "\n".join(metadata) + "\n\n"
        
        # Add content
        post_md += "**Content**:\n"
        if escaped_content:
            post_md += f"> {escaped_content}\n\n"
        else:
            post_md += "> *No text content*\n\n"
        
        # Add images if present
        if post.images:
            post_md += "**Images**:\n"
            for img_url in post.images:
                post_md += f"- ![Post Image]({img_url})\n"
            post_md += "\n"
        
        # Add hashtags if present
        if post.hashtags:
            post_md += f"**Hashtags**: {' '.join(post.hashtags)}\n\n"
        
        # Add mentions if present
        if post.mentions:
            post_md += f"**Mentions**: {' '.join(post.mentions)}\n\n"
        
        # Add external links if present
        if post.external_links:
            post_md += "**External Links**:\n"
            for link in post.external_links:
                post_md += f"- {link}\n"
            post_md += "\n"
        
        # Add post URL if available
        if post.post_url:
            post_md += f"[View Original Post]({post.post_url})\n\n"
        
        post_md += "---\n"
        return post_md
    
    def _escape_markdown(self, text: str) -> str:
        """
        Escape Markdown special characters in text.
        
        Args:
            text: Raw text content
            
        Returns:
            Escaped text safe for Markdown
        """
        if not text:
            return ""
        
        # Characters that need escaping in Markdown
        escape_chars = r'\\`*_{}[]()#+-.!|'
        
        # Escape each character
        escaped = text
        for char in escape_chars:
            escaped = escaped.replace(char, f'\\{char}')
        
        return escaped
    
    def _generate_footer(self, posts: List[PostData]) -> str:
        """
        Generate the footer section.
        
        Args:
            posts: List of PostData objects
            
        Returns:
            Footer content as string
        """
        footer = f"""

---

## 📄 Export Information

- **Total Posts Exported**: {len(posts)}
- **Export Date**: {datetime.now().strftime("%B %d, %Y at %H:%M")}
- **Generated by**: LinkedIn Post Extractor
- **Format**: Markdown with YAML frontmatter

### Notes

- This export contains public posts visible at the time of extraction
- Post engagement metrics may not be complete due to LinkedIn's privacy settings
- Images and external links are referenced but not downloaded
- Timestamps are converted to local time

---

*This file was automatically generated. Please refer to the original LinkedIn profile for the most up-to-date information.*
"""
        return footer
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get generation statistics.
        
        Returns:
            Dictionary with generation statistics
        """
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset generation statistics."""
        self.stats = {
            'files_created': 0,
            'posts_processed': 0,
            'errors': 0
        }


def generate_markdown_from_posts(
    posts: List[PostData],
    profile_name: str,
    profile_url: str,
    output_dir: str = ".",
    filename: Optional[str] = None
) -> str:
    """
    Convenience function to generate Markdown from posts.
    
    Args:
        posts: List of PostData objects
        profile_name: Name of the LinkedIn profile
        profile_url: URL of the LinkedIn profile
        output_dir: Output directory for the file
        filename: Custom filename (optional)
        
    Returns:
        Path to the generated Markdown file
    """
    generator = MarkdownGenerator(output_dir)
    return generator.generate_markdown_file(posts, profile_name, profile_url, filename)


def preview_markdown_content(
    posts: List[PostData],
    profile_name: str,
    profile_url: str,
    max_posts: int = 3
) -> str:
    """
    Generate a preview of the Markdown content without saving to file.
    
    Args:
        posts: List of PostData objects
        profile_name: Name of the LinkedIn profile
        profile_url: URL of the LinkedIn profile
        max_posts: Maximum number of posts to include in preview
        
    Returns:
        Preview of Markdown content
    """
    # Limit posts for preview
    preview_posts = posts[:max_posts] if posts else []
    
    generator = MarkdownGenerator()
    content = generator._generate_markdown_content(preview_posts, profile_name, profile_url)
    
    if len(posts) > max_posts:
        content += f"\n\n*... and {len(posts) - max_posts} more posts*\n"
    
    return content
