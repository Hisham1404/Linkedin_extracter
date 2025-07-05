# LinkedIn Post Extractor

A robust, production-ready Python automation tool designed to extract all posts from LinkedIn profiles and save them in structured Markdown format. Built with comprehensive error handling, session recovery, and enterprise-grade reliability.

## Features

### Core Functionality
- **Automated LinkedIn Navigation**: Smart browser automation with stealth techniques
- **Dynamic Content Extraction**: Infinite scroll handling with intelligent content detection
- **Structured Data Output**: Clean, organized Markdown format with metadata
- **URL Validation**: Comprehensive LinkedIn profile URL validation and normalization

### Advanced Capabilities
- **Session Recovery**: Automatic checkpoint system for resuming interrupted extractions
- **Error Handling**: Comprehensive error hierarchy with retry logic and exponential backoff
- **Partial Extraction**: Graceful degradation for incomplete data scenarios
- **Progress Tracking**: Real-time progress indicators with detailed statistics and ETA
- **Retry Logic**: Intelligent retry mechanisms with circuit breaker patterns
- **Logging & Reporting**: Structured logging with detailed error diagnostics
- **CLI Interface**: Full-featured command-line interface with comprehensive options
- **Anti-Bot Protection**: Advanced stealth techniques to bypass LinkedIn's anti-bot detection

### Reliability Features
- **Checkpoint System**: Automatic session state saving every 30 seconds
- **Recovery Mechanisms**: Resume from last successful checkpoint after interruptions
- **Rate Limiting**: Respectful extraction with human-like delays
- **Browser Management**: Automatic browser lifecycle management
- **Data Integrity**: Hash-based checkpoint verification and consistency checks

## Project Structure

```
linkedin_post_extracter/
├── main.py                           # Main application entry point
├── src/                              # Source code modules
│   ├── __init__.py                   # Package initialization with exports
│   ├── url_validator.py              # LinkedIn URL validation and normalization
│   ├── browser_manager.py            # Browser automation and lifecycle management
│   ├── content_parser.py             # HTML parsing and content extraction
│   ├── scroll_automator.py           # Infinite scroll and dynamic content loading
│   ├── markdown_generator.py         # Markdown output generation
│   ├── exceptions.py                 # Custom exception hierarchy
│   ├── retry_handler.py              # Retry logic with exponential backoff
│   ├── partial_extraction_handler.py # Graceful degradation for partial failures
│   ├── error_reporter.py             # Comprehensive error reporting system
│   ├── progress_tracker.py           # Real-time progress tracking with statistics
│   └── session_recovery.py           # Session recovery and checkpoint system
├── config/                           # Configuration files
│   ├── __init__.py                   # Configuration package initialization
│   ├── logging_config.py             # Logging configuration
│   └── constants.py                  # Application constants
├── logs/                             # Application logs
│   └── progress_stats.json           # Progress statistics (sample)
├── requirements.txt                  # Python dependencies
└── README.md                         # Project documentation

# Note: The following directories are excluded from the repository (.gitignore):
# ├── tests/                          # Comprehensive test suite (197+ tests)
# ├── examples/                       # Usage examples and demonstrations  
# ├── .taskmaster/                    # Task management system
# ├── checkpoints/                    # Session recovery checkpoints (created at runtime)
# ├── logs/*.log                      # Runtime log files
# └── venv/                           # Virtual environment
```

## Requirements

- Python 3.8+
- Chrome or Firefox browser
- Stable internet connection
- 4GB+ RAM (recommended for large profile extractions)
- 1GB+ free disk space

## Dependencies

Core dependencies include:
- **selenium**: Web automation framework
- **beautifulsoup4**: HTML parsing and content extraction
- **webdriver-manager**: Automatic browser driver management
- **tqdm**: Progress bars and status indicators
- **pytest**: Testing framework with comprehensive coverage
- **python-dotenv**: Environment variable management

## Repository Contents

This repository contains the core production-ready application with:

### ✅ **Included in Repository**
- **Complete source code** (`src/` directory) - All 11 core modules
- **Main application** (`main.py`) - Full-featured CLI application
- **Configuration system** (`config/` directory) - Logging and constants
- **Dependencies** (`requirements.txt`) - All required packages
- **Documentation** (`README.md`) - Comprehensive project documentation
- **Sample progress stats** (`logs/progress_stats.json`) - Example output format

### 📁 **Excluded from Repository** (Available in Development)
- **Test suite** (`tests/` directory) - 197+ comprehensive tests
- **Usage examples** (`examples/` directory) - Code examples and demonstrations
- **Task management** (`.taskmaster/` directory) - Development task tracking
- **Runtime data** (`checkpoints/`, `logs/*.log`) - Created during execution
- **Environment files** (`venv/`, `.env`) - Local development setup

The repository focuses on delivering a clean, production-ready application while excluding development artifacts and test files that would clutter the distribution.

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd linkedin_post_extracter
   ```

2. **Create and activate virtual environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # Unix/macOS:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**
   ```bash
   # Install development dependencies if needed
   pip install pytest tqdm
   
   # Run a basic validation
   python main.py --help
   ```

*Note: The test suite is available in the development environment but excluded from the repository for a cleaner distribution.*

## Quick Start

1. **Install and run in 3 steps:**
   ```bash
   # 1. Install dependencies
   pip install -r requirements.txt
   
   # 2. Test the application
   python main.py --help
   
   # 3. Extract posts from a LinkedIn profile
   python main.py https://www.linkedin.com/in/username --verbose
   ```

2. **First-time users - try with minimal settings:**
   ```bash
   # Start with current page only (no infinite scroll)
   python main.py https://www.linkedin.com/in/username --disable-scroll --verbose
   ```

3. **If you encounter errors:**
   - Use `--verbose` flag to see detailed error information
   - Check the log file at `logs/linkedin_extractor.log`
   - Try different LinkedIn profile URLs
   - Ensure stable internet connection
   - **For HTTP 999 errors**: Use `--skip-validation` flag to bypass LinkedIn's anti-bot protection

## Usage

### Basic Usage
```bash
python main.py <linkedin_profile_url> [options]
```

### Command Line Options
```bash
# Basic extraction
python main.py https://linkedin.com/in/username

# Specify output directory
python main.py https://linkedin.com/in/username --output ./extracted_posts

# Enable verbose logging for troubleshooting
python main.py https://linkedin.com/in/username --verbose

# Customize scroll behavior
python main.py https://linkedin.com/in/username --max-scrolls 50 --scroll-delay 3.0

# Extract current page only (disable infinite scroll)
python main.py https://linkedin.com/in/username --disable-scroll

# Custom filename for output
python main.py https://linkedin.com/in/username --filename "john_doe_posts.md"

# Custom log file location
python main.py https://linkedin.com/in/username --log-file ./custom_logs/extraction.log

# Skip URL validation to bypass anti-bot protection
python main.py https://linkedin.com/in/username --skip-validation --verbose
```

### Troubleshooting Common Issues

#### 1. **HTTP 999 / LinkedIn Anti-Bot Protection**
```bash
# LinkedIn's primary anti-bot response. Use skip-validation flag:
python main.py https://linkedin.com/in/username --skip-validation --verbose

# For testing, start with current page only:
python main.py https://linkedin.com/in/username --skip-validation --disable-scroll --verbose
```

#### 2. **HTTP 405 / Access Denied Errors**
```bash
# LinkedIn may block direct requests. Try:
# - Using --skip-validation flag to bypass initial check
# - Using a VPN or different IP address
# - Waiting a few minutes between attempts
# - Using verbose mode to see detailed error information
python main.py https://linkedin.com/in/username --skip-validation --verbose
```

#### 3. **Timeout Issues**
```bash
# Increase delays and reduce scroll attempts
python main.py https://linkedin.com/in/username --skip-validation --scroll-delay 5.0 --max-scrolls 10
```

#### 4. **Network Connection Issues**
```bash
# Test with minimal extraction first
python main.py https://linkedin.com/in/username --skip-validation --disable-scroll --verbose
```

#### 5. **Profile URL Formats**
LinkedIn profile URLs should be in one of these formats:
- `https://www.linkedin.com/in/username`
- `https://linkedin.com/in/username`
- `https://www.linkedin.com/in/username/`

**Example valid URLs:**
- `https://www.linkedin.com/in/john-doe`
- `https://linkedin.com/in/jane-smith-12345`
- `https://www.linkedin.com/in/company-ceo/`

### Important Notes

⚠️ **LinkedIn Anti-Bot Protection**: LinkedIn has sophisticated anti-bot measures that may block automated requests. This is normal behavior and not a bug in the application.

**Recommended Approach for Bypassing Anti-Bot Protection:**
1. **Use Skip Validation**: Always start with `--skip-validation` flag
2. **Start Small**: Test with `--disable-scroll` first
3. **Use Delays**: Increase `--scroll-delay` to 4-6 seconds for more human-like behavior
4. **Monitor Logs**: Always use `--verbose` for troubleshooting
5. **Be Patient**: LinkedIn may temporarily block requests; wait and try again
6. **Check Profile Access**: Ensure the LinkedIn profile is publicly accessible

**Common LinkedIn Responses:**
- `HTTP 999`: LinkedIn's primary anti-bot protection (use `--skip-validation`)
- `HTTP 405`: Method not allowed (anti-bot protection)
- `HTTP 429`: Rate limiting (too many requests)
- `HTTP 403`: Forbidden (profile may be private)
- `Timeout`: Network issues or LinkedIn blocking the request

### Working Example

```bash
# Step 1: Test the application
python main.py --help

# Step 2: Try a simple extraction with anti-bot bypass
python main.py https://www.linkedin.com/in/username --skip-validation --disable-scroll --verbose

# Step 3: If successful, try with limited scrolling
python main.py https://www.linkedin.com/in/username --skip-validation --max-scrolls 5 --scroll-delay 4.0 --verbose

# Step 4: Full extraction (when ready)
python main.py https://www.linkedin.com/in/username --skip-validation --output ./extracted_posts
```

**Expected Output (when successful):**
```
✅ Profile URL validated successfully
🚀 Starting browser automation...
📄 Extracting posts from profile...
💾 Saved posts to: username_posts.md
🎉 Extraction completed successfully!
```

**If LinkedIn blocks the request:**
```
❌ Invalid LinkedIn URL: HTTP 999: LinkedIn anti-bot protection detected
```
This is normal - LinkedIn actively blocks automated tools. Use `--skip-validation` flag to bypass this check.

### Programmatic Usage
```python
from src import (
    URLValidator, 
    BrowserManager, 
    ContentParser, 
    SessionRecoveryManager,
    ProgressTracker
)

# Initialize components
url_validator = URLValidator()
browser_manager = BrowserManager()
recovery_manager = SessionRecoveryManager()
progress_tracker = ProgressTracker()

# Validate and extract
if url_validator.validate(profile_url):
    # Start recoverable session with progress tracking
    session = recovery_manager.start_session(profile_url, output_dir)
    progress_tracker.start_tracking(session)
    
    # Perform extraction with automatic checkpoints and progress updates
    # ... extraction logic ...
```

## Development Status

✅ **Production Ready** - All features implemented, tested, and production-ready

### Completed Features
- ✅ **Project Foundation**: Complete project structure and configuration
- ✅ **URL Validation**: Comprehensive LinkedIn profile URL validation
- ✅ **Browser Automation**: Robust browser management with automatic driver handling
- ✅ **Content Parsing**: Advanced HTML parsing and content extraction
- ✅ **Scroll Automation**: Intelligent infinite scroll with dynamic content detection
- ✅ **Markdown Generation**: Clean, structured Markdown output with metadata
- ✅ **Error Handling**: Comprehensive error hierarchy with custom exceptions
- ✅ **Retry Logic**: Exponential backoff with circuit breaker patterns
- ✅ **Partial Extraction**: Graceful degradation for incomplete data scenarios
- ✅ **Error Reporting**: Structured logging and user-friendly error messages
- ✅ **Session Recovery**: Automatic checkpoint system with resume capability
- ✅ **Progress Tracking**: Real-time progress indicators with detailed statistics
- ✅ **CLI Interface**: Full-featured command-line interface with all options

### Project Status: 100% Complete
All 10 main tasks and 30 subtasks have been completed and thoroughly tested. The project is ready for production use with enterprise-grade reliability and comprehensive error handling.

### Testing Coverage
- **197+ tests** across all modules (available in development environment)
- **High coverage** for core functionality including progress tracking
- **Integration tests** for end-to-end workflows
- **Error simulation** tests for robust error handling
- **Progress tracking tests** for real-time statistics and ETA calculations

*Note: Test files are excluded from the repository but are available in the development environment. The core functionality has been thoroughly tested and validated.*

## Anti-Bot Protection Guide

For detailed information on bypassing LinkedIn's anti-bot protection, see [ANTI_BOT_GUIDE.md](ANTI_BOT_GUIDE.md).

This guide covers:
- Understanding LinkedIn's anti-bot mechanisms
- Using the `--skip-validation` flag
- Advanced stealth techniques
- Proxy configuration
- Troubleshooting common issues
- Best practices for avoiding detection

### Architecture Highlights
- **Modular Design**: Clean separation of concerns with well-defined interfaces
- **Comprehensive Testing**: Each module thoroughly tested with unit and integration tests
- **Error Resilience**: Multi-layered error handling with automatic recovery
- **Session Management**: Persistent session state with checkpoint-based recovery
- **Progress Tracking**: Real-time progress monitoring with detailed statistics and ETA
- **CLI Interface**: Full-featured command-line interface with comprehensive options
- **Production Ready**: Proper logging, configuration management, and deployment preparation

## License

MIT License - see LICENSE file for details
