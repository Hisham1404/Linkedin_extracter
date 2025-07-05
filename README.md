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
- **Progress Tracking**: Real-time progress indicators and status updates
- **Retry Logic**: Intelligent retry mechanisms with circuit breaker patterns
- **Logging & Reporting**: Structured logging with detailed error diagnostics

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
│   └── session_recovery.py           # Session recovery and checkpoint system
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
│   ├── test_session_recovery.py      # Session recovery tests
│   └── integration_test_*.py         # Integration test suites
├── config/                           # Configuration files
│   ├── logging_config.py             # Logging configuration
│   └── constants.py                  # Application constants
├── examples/                         # Usage examples and demonstrations
│   ├── retry_handler_examples.py     # Retry logic integration examples
│   └── partial_extraction_examples.py # Partial extraction examples
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
```

### Programmatic Usage
```python
from src import (
    URLValidator, 
    BrowserManager, 
    ContentParser, 
    SessionRecoveryManager
)

# Initialize components
url_validator = URLValidator()
browser_manager = BrowserManager()
recovery_manager = SessionRecoveryManager()

# Validate and extract
if url_validator.validate(profile_url):
    # Start recoverable session
    session = recovery_manager.start_session(profile_url, output_dir)
    
    # Perform extraction with automatic checkpoints
    # ... extraction logic ...
```

## Development Status

✅ **Production Ready** - Core functionality implemented and tested

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

### Current Phase: Progress Tracking Implementation
- 🔄 **In Progress**: Real-time progress indicators and user feedback system
- 📋 **Next**: Enhanced CLI interface with improved user experience

### Testing Coverage
- **197 tests** across all modules
- **High coverage** for core functionality
- **Integration tests** for end-to-end workflows
- **Error simulation** tests for robust error handling

### Architecture Highlights
- **Modular Design**: Clean separation of concerns with well-defined interfaces
- **Comprehensive Testing**: Each module thoroughly tested with unit and integration tests
- **Error Resilience**: Multi-layered error handling with automatic recovery
- **Session Management**: Persistent session state with checkpoint-based recovery
- **Production Ready**: Proper logging, configuration management, and deployment preparation

## License

MIT License - see LICENSE file for details
