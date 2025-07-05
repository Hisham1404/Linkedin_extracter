#!/usr/bin/env python3
"""
LinkedIn Post Extractor - Main Entry Point

This module serves as the main entry point for the LinkedIn Post Extractor application.
It handles command-line arguments, coordinates the extraction process, and manages
the overall application flow.
"""

import sys
import argparse
from pathlib import Path

# Add src and config directories to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "config"))

# Import configuration and modules
from config import configure_logging, get_logger, APP_NAME, APP_VERSION
from url_validator import validate_linkedin_url, suggest_url_corrections
from browser_manager import WebDriverManager
from content_parser import parse_linkedin_profile, extract_post_summary
from markdown_generator import generate_markdown_from_posts
from scroll_automator import create_scroll_automator

# Import error handling system
from error_reporter import ErrorReporter, ErrorSeverity, create_error_reporter
from exceptions import (
    LinkedInExtractorError, NetworkError, ValidationError, 
    BrowserError, ExtractionError
)


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        prog=APP_NAME,
        description="Extract posts from LinkedIn profiles and save as Markdown files",
        epilog=f"Version: {APP_VERSION}"
    )
    parser.add_argument(
        "profile_url",
        help="LinkedIn profile URL to extract posts from"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output directory for generated files (default: current directory)",
        default="."
    )
    parser.add_argument(
        "--filename", "-f",
        help="Custom filename for the output file (optional)",
        default=None
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--log-file", "-l",
        help="Log file path (default: logs/linkedin_extractor.log)",
        default="logs/linkedin_extractor.log"
    )
    parser.add_argument(
        "--max-scrolls",
        type=int,
        help="Maximum number of scroll actions to perform (default: 30)",
        default=30
    )
    parser.add_argument(
        "--scroll-delay",
        type=float,
        help="Delay between scroll actions in seconds (default: 2.0)",
        default=2.0
    )
    parser.add_argument(
        "--disable-scroll",
        action="store_true",
        help="Disable infinite scroll automation (extract current page only)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = configure_logging(
        verbose=args.verbose,
        log_file=args.log_file
    )
    
    # Setup error reporting
    error_reporter = create_error_reporter(
        log_file=args.log_file.replace('.log', '_errors.log'),
        include_system_info=True
    )
    
    logger.info(f"{APP_NAME} v{APP_VERSION} started")
    logger.info(f"Profile URL: {args.profile_url}")
    logger.info(f"Output directory: {args.output}")
    logger.info(f"Verbose mode: {args.verbose}")
    
    try:
        # Step 1: Validate LinkedIn URL
        logger.info("Validating LinkedIn profile URL...")
        try:
            is_valid, normalized_url, validation_error = validate_linkedin_url(
                args.profile_url, 
                check_accessibility=True
            )
            
            if not is_valid:
                error = ValidationError(f"URL validation failed: {validation_error}")
                context = error_reporter.create_error_context(
                    module_name="main",
                    function_name="main",
                    user_action="URL validation",
                    input_data={"url": args.profile_url}
                )
                error_reporter.report_error(error, context)
                
                logger.error(f"URL validation failed: {validation_error}")
                print(f"❌ Invalid LinkedIn URL: {validation_error}")
                
                # Provide suggestions for correction
                suggestions = suggest_url_corrections(args.profile_url)
                if suggestions:
                    print(f"\n💡 Did you mean one of these?")
                    for i, suggestion in enumerate(suggestions, 1):
                        print(f"   {i}. {suggestion}")
                
                return 1
                
        except Exception as e:
            error = ValidationError(f"URL validation error: {e}")
            context = error_reporter.create_error_context(
                module_name="main",
                function_name="main",
                user_action="URL validation",
                input_data={"url": args.profile_url}
            )
            error_reporter.report_error(error, context)
            logger.error(f"URL validation error: {e}")
            print(f"❌ URL validation error: {e}")
            return 1
        
        logger.info(f"URL validation successful: {normalized_url}")
        print(f"✅ LinkedIn URL validated: {normalized_url}")
        
        # Step 2: Initialize WebDriver for content extraction
        logger.info("Initializing web browser...")
        print("🌐 Starting web browser...")
        
        try:
            with WebDriverManager(headless=True) as driver_manager:
                # Step 3: Navigate to LinkedIn profile
                logger.info(f"Navigating to LinkedIn profile: {normalized_url}")
                print("📖 Loading LinkedIn profile...")
                
                if not driver_manager.navigate_to_url(normalized_url):
                    logger.error("Failed to navigate to LinkedIn profile")
                    print("❌ Failed to load LinkedIn profile")
                    return 1
                
                # Step 4: Perform infinite scroll to load all content
                if not args.disable_scroll:
                    logger.info("Performing infinite scroll to load all posts...")
                    print("🔄 Loading all posts (this may take a moment)...")
                    
                    try:
                        # Create scroll automator with optimized settings
                        scroll_automator = create_scroll_automator(
                            driver_manager.driver,
                            max_scrolls=args.max_scrolls,  # User-defined limit
                            scroll_pause_time=args.scroll_delay,  # User-defined timing
                            content_wait_timeout=5,
                            human_like_scrolling=True,
                            debug_mode=args.verbose
                        )
                        
                        # Perform infinite scroll
                        scroll_result = scroll_automator.scroll_to_load_all_content()
                        
                        if scroll_result['success']:
                            stats = scroll_result['stats']
                            logger.info(f"Infinite scroll completed: {stats['total_scrolls']} scrolls, "
                                       f"{stats['content_loads']} content loads")
                            print(f"✅ Loaded content with {stats['total_scrolls']} scroll actions")
                            
                            if args.verbose:
                                print(f"   • Content loads detected: {stats['content_loads']}")
                                print(f"   • Retries performed: {stats.get('retries', 0)}")
                                if stats.get('duplicates_detected', 0) > 0:
                                    print(f"   • Duplicate content detected: {stats['duplicates_detected']}")
                        else:
                            logger.warning(f"Infinite scroll failed: {scroll_result.get('error', 'Unknown error')}")
                            print("⚠️  Infinite scroll failed, proceeding with current page content")
                            if args.verbose:
                                print(f"   Error: {scroll_result.get('error', 'Unknown error')}")
                    
                    except Exception as scroll_error:
                        logger.warning(f"Scroll automation error: {scroll_error}")
                        print("⚠️  Scroll automation failed, proceeding with current page content")
                        if args.verbose:
                            print(f"   Error: {scroll_error}")
                
                # Step 5: Extract page content
                logger.info("Extracting page content...")
                print("🔍 Analyzing page content...")
                
                page_source = driver_manager.get_page_source()
                if not page_source:
                    logger.error("Failed to extract page source")
                    print("❌ Failed to extract page content")
                    return 1
                
                # Step 6: Parse content and extract posts
                logger.info("Parsing LinkedIn posts...")
                print("📝 Extracting posts...")
                
                posts = parse_linkedin_profile(page_source)
                
                if not posts:
                    logger.warning("No posts found on the profile")
                    print("⚠️  No posts found on this LinkedIn profile")
                    print("   This could be due to:")
                    print("   • The profile has no public posts")
                    print("   • The profile requires login to view posts")
                    print("   • LinkedIn's structure has changed")
                    return 0
                
                # Step 6: Generate summary
                summary = extract_post_summary(posts)
                logger.info(f"Extracted {summary['total_posts']} posts")
                
                # Display results
                print(f"\n🎉 Successfully extracted {summary['total_posts']} posts!")
                print(f"📊 Post Summary:")
                print(f"   • Total posts: {summary['total_posts']}")
                if summary.get('post_types'):
                    print(f"   • Post types: {dict(summary['post_types'])}")
                if summary.get('unique_hashtags'):
                    print(f"   • Unique hashtags: {summary['unique_hashtags']}")
                if summary.get('unique_authors'):
                    print(f"   • Authors: {summary['unique_authors']}")
                
                # Step 7: Generate Markdown file
                logger.info("Generating Markdown file...")
                print("📄 Creating Markdown file...")
                
                try:
                    # Extract profile name from URL for markdown generation
                    profile_name = normalized_url.split('/')[-1] or normalized_url.split('/')[-2]
                    if not profile_name:
                        profile_name = "linkedin-profile"
                    
                    # Generate markdown file
                    output_file = generate_markdown_from_posts(
                        posts=posts,
                        profile_name=profile_name,
                        profile_url=normalized_url,
                        output_dir=args.output,
                        filename=args.filename
                    )
                    
                    logger.info(f"Markdown file generated: {output_file}")
                    print(f"✅ Markdown file created: {output_file}")
                    
                except Exception as e:
                    logger.error(f"Failed to generate Markdown file: {e}", exc_info=True)
                    print(f"❌ Failed to create Markdown file: {e}")
                    return 1
                
        except Exception as e:
            logger.error(f"Web automation error: {e}", exc_info=True)
            print(f"❌ Web automation error: {e}")
            return 1
        
        logger.info("Application completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
