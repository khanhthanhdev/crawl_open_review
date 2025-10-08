

A comprehensive Python crawler for extracting academic papers, reviews, comments, and metadata from OpenReview conferences (ICLR, NeurIPS, ICML, etc.). Built for researchers, analysts, and anyone interested in academic peer review data.

## Features

- **Multi-Conference Support**: Crawl ICLR, NeurIPS, ICML, and other OpenReview venues
- **Complete Data Extraction**: Papers, reviews, comments, rebuttals, and meta-reviews
- **Dual API Support**: Automatic fallback between OpenReview API v1 and v2
- **Smart Content Detection**: Identifies reviews/comments based on content structure (not just invitation strings)
- **Rate Limiting**: Respects API limits with configurable delays
- **Flexible Filtering**: Crawl all papers or filter for accepted papers only
- **Multiple Output Formats**: JSON (complete data) and CSV (summaries)
- **Progress Tracking**: Real-time progress bars and detailed logging
- **Error Recovery**: Robust error handling with retry logic
- **Data Validation**: Ensures data completeness and quality

## Installation

### Prerequisites
- Python 3.8 or higher
- OpenReview account (for API access)

### Install with uv (Recommended)
```bash
# Clone the repository
git clone https://github.com/yourusername/openreview-crawler.git
cd openreview-crawler

# Install dependencies
uv sync
```

### Install with pip
```bash
# Clone the repository
git clone https://github.com/yourusername/openreview-crawler.git
cd openreview-crawler

# Install dependencies
pip install -r requirements.txt
```

### Install with pip (Development)
```bash
pip install -e .
```

## 🚀 Quick Start

1. **Set up your OpenReview credentials:**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenReview username and password
   ```

2. **Run your first crawl:**
   ```bash
   python crawl.py
   ```

3. **View the results:**
   - Complete data: `iclr_2024_papers_reviews_accepted.json`
   - Summary table: `iclr_2024_papers_summary_accepted.csv`

## Configuration

### Environment Variables (.env)
```bash
# Required: OpenReview API credentials
OPENREVIEW_USERNAME="your@email.com"
OPENREVIEW_PASSWORD="your_password"

# Optional: Rate limiting (requests per second)
OPENREVIEW_RATE_LIMIT=3

# Optional: Output directories
OUTPUT_DIR="output"
DATA_DIR="data"
```

### Command Line Options
```bash
python crawl.py --help
```

Available options:
- `--year`: Conference year (default: 2024)
- `--venue`: Conference venue (default: ICLR)
- `--accepted-only`: Only crawl accepted papers
- `--output-dir`: Output directory
- `--max-papers`: Limit number of papers (for testing)

## Usage Examples

### Basic ICLR Crawl
```python
from crawl import crawl_iclr_papers_and_reviews

# Crawl all ICLR 2024 papers
data = crawl_iclr_papers_and_reviews(year=2024, accepted_only=False)

# Crawl only accepted papers
accepted_data = crawl_iclr_papers_and_reviews(year=2024, accepted_only=True)
```

### Command Line Usage
```bash
# Crawl ICLR 2024 accepted papers only
python crawl.py --year 2024 --accepted-only

# Crawl NeurIPS 2023 (if supported)
python crawl.py --venue neurips --year 2023

# Test with limited papers
python crawl.py --max-papers 10
```

### Advanced Usage
```python
from crawl import get_openreview_client, save_data

# Get API client
client, api_version = get_openreview_client()

# Custom crawling logic
# ... your code here ...

# Save data
save_data(data, year=2024, accepted_only=True)
```

## Data Formats

### JSON Output Structure
```json
{
  "paper_id": "ICLR.cc/2024/Conference/1234",
  "forum_id": "ICLR.cc/2024/Conference/1234",
  "title": "Deep Learning Paper Title",
  "abstract": "Abstract text...",
  "authors": ["Author One", "Author Two"],
  "keywords": ["deep learning", "neural networks"],
  "pdf_url": "https://openreview.net/pdf?id=...",
  "forum_url": "https://openreview.net/forum?id=...",
  "reviews": [
    {
      "review_id": "review_123",
      "rating": "8: Accept",
      "confidence": "4: High",
      "summary": "Summary of the review...",
      "soundness": "3: Good",
      "presentation": "3: Good",
      "contribution": "3: Good",
      "strengths": "Strengths text...",
      "weaknesses": "Weaknesses text...",
      "review_text": "Full review text..."
    }
  ],
  "num_reviews": 4,
  "comments": [
    {
      "note_id": "comment_456",
      "comment": "Author response text...",
      "content": {...}
    }
  ],
  "meta_reviews": [...],
  "decision": "Accept (poster)"
}
```

### CSV Summary Format
| paper_id | title | authors | num_reviews | avg_rating | decision | keywords | forum_url |
|----------|-------|---------|-------------|------------|----------|----------|-----------|
| ICLR.cc/2024/... | Paper Title | Author One, Author Two | 4 | 7.5 | Accept (poster) | deep learning | https://... |

## API Reference

### Core Functions

#### `crawl_iclr_papers_and_reviews(year, accepted_only=False)`
Crawls ICLR papers and their reviews.

**Parameters:**
- `year` (int): Conference year (e.g., 2024)
- `accepted_only` (bool): If True, only return accepted papers

**Returns:** List of paper dictionaries with reviews and metadata

#### `get_openreview_client()`
Creates and returns an OpenReview API client.

**Returns:** Tuple of (client, api_version) where api_version is 'v1' or 'v2'

#### `save_data(data, year, accepted_only=False)`
Saves crawled data to JSON and CSV files.

**Parameters:**
- `data` (list): List of paper dictionaries
- `year` (int): Conference year
- `accepted_only` (bool): Whether data contains only accepted papers

### Utility Functions

#### `is_accepted_paper(decision)`
Determines if a paper is accepted based on its decision string.

**Parameters:**
- `decision` (str): Decision text from meta-review

**Returns:** Boolean indicating acceptance

## Troubleshooting

### Common Issues

#### "No papers found" Error
- Check if the conference year is correct
- Verify the conference has been published on OpenReview
- Some conferences use different invitation patterns

#### Authentication Errors
- Verify your OpenReview credentials in `.env`
- Ensure your account has access to the conference
- Check if your password contains special characters

#### Rate Limiting
- The crawler includes automatic rate limiting (0.3s between requests)
- If you get rate limit errors, increase the delay in the code
- Consider running during off-peak hours

#### Empty Reviews/Comments
- This was fixed in the latest version - the crawler now detects content by structure
- If you still see this, check the API version being used
- Some conferences may have different review formats

### Debug Mode
Enable debug output to troubleshoot issues:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Getting Help
1. Check the [Issues](https://github.com/yourusername/openreview-crawler/issues) page
2. Review the [documentation](docs/document.md) for detailed architecture
3. Run with `--help` for command-line options

## Project Structure

```
openreview-crawler/
├── crawl.py              # Main crawling script
├── main.py               # Simple extraction script
├── pyproject.toml        # Project configuration
├── uv.lock              # Dependency lock file
├── .env                 # Environment variables (create from .env.example)
├── README.md            # This file
├── docs/
│   └── document.md      # Detailed architecture documentation
├── data/                # Raw crawled data
├── output/              # Processed outputs
├── notebooks/           # Jupyter notebooks for analysis
└── src/                 # Source code (future modular structure)
    ├── crawler/
    ├── parsers/
    ├── storage/
    └── utils/
```

## Contributing


### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/openreview-crawler.git
cd openreview-crawler

# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .
```

### Code Style
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions
- Add tests for new features
