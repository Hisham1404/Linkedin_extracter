# LinkedIn Post Extractor

A Python-based automation tool designed to extract all posts from a specified LinkedIn profile and save them in a structured Markdown format.

## Features

- Automated navigation to LinkedIn profiles
- Dynamic content extraction with infinite scroll handling
- Structured data output in Markdown format
- Error handling and user feedback
- Local file storage with organized naming conventions

## Project Structure

```
linkedin_post_extracter/
├── main.py                 # Main application entry point
├── src/                    # Source code modules
│   └── __init__.py
├── tests/                  # Test files
│   └── __init__.py
├── config/                 # Configuration files
├── logs/                   # Log files
├── requirements.txt        # Python dependencies
└── README.md              # Project documentation
```

## Requirements

- Python 3.8+
- Chrome or Firefox browser
- Stable internet connection

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/macOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Usage

```bash
python main.py <linkedin_profile_url> [--output output_directory] [--verbose]
```

## Development Status

🚧 **In Development** - This project is currently under active development.

Current Phase: Project Foundation Setup

## License

MIT License - see LICENSE file for details
