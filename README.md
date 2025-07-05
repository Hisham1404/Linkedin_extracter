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
│   ├── session_recovery.py           # Session recovery and checkpoint system
├── tests/                            # Comprehensive test suite (197 tests)
│   ├── __init__.py                   # Test package initialization
│   ├── test_url_validator.py         # URL validation tests
│   ├── test_browser_manager.py       # Browser management tests
│   ├── test_content_parser.py        # Content parsing tests
│   ├── test_scroll_automator.py      # Scroll automation tests
│   ├── test_markdown_generator.py    # Markdown generation tests
│   ├── test_exceptions.py            # Exception handling tests
│   ├── test_retry_handler.py         # Retry logic tests
│   ├── test_partial_extraction_handler.py # Partial extraction tests
│   ├── test_error_reporter.py        # Error reporting tests
│   ├── test_progress_tracker.py      # Progress tracking tests
│   ├── test_session_recovery.py      # Session recovery tests
│   └── integration_test_*.py         # Integration test suites
├── config/                           # Configuration files
│   ├── logging_config.py             # Logging configuration
│   └── constants.py                  # Application constants
├── examples/                         # Usage examples and demonstrations
│   ├── retry_handler_examples.py     # Retry logic integration examples
│   ├── partial_extraction_examples.py # Partial extraction examples
│   ├── progress_tracker_examples.py  # Progress tracking examples
│   └── advanced_rate_calculation_examples.py # Advanced rate calculation examples
├── logs/                             # Application logs
├── checkpoints/                      # Session recovery checkpoints
├── .taskmaster/                      # Task management system
├── requirements.txt                  # Python dependencies
├── .gitignore                        # Git ignore configuration
└── README.md                         # Project documentation
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
   python -m pytest tests/ -v
   ```

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

# Enable verbose logging
python main.py https://linkedin.com/in/username --verbose

# Resume from checkpoint
python main.py https://linkedin.com/in/username --resume

# Set custom scroll delay (human-like behavior)
python main.py https://linkedin.com/in/username --scroll-delay 2.5

# Enable progress tracking with detailed statistics
python main.py https://linkedin.com/in/username --progress

# Set custom timeout values
python main.py https://linkedin.com/in/username --timeout 30
```

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
- **197+ tests** across all modules
- **High coverage** for core functionality including progress tracking
- **Integration tests** for end-to-end workflows
- **Error simulation** tests for robust error handling
- **Progress tracking tests** for real-time statistics and ETA calculations

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
