# OpenReview Crawler - Project Structure & Pipeline

## 📁 Recommended Project Structure

```
openreview-crawler/
│
├── config/
│   ├── __init__.py
│   ├── settings.py              # Configuration settings
│   └── venues.yaml              # Conference venues configuration
│
├── src/
│   ├── __init__.py
│   │
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── base_crawler.py      # Base crawler class
│   │   ├── iclr_crawler.py      # ICLR-specific crawler
│   │   ├── neurips_crawler.py   # NeurIPS crawler
│   │   └── icml_crawler.py      # ICML crawler
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── paper_parser.py      # Parse paper metadata
│   │   ├── review_parser.py     # Parse review content
│   │   └── comment_parser.py    # Parse comments/rebuttals
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── file_storage.py      # Save to JSON/CSV
│   │   ├── db_storage.py        # Save to database
│   │   └── cloud_storage.py     # Upload to S3/GCS (optional)
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── rate_limiter.py      # API rate limiting
│   │   ├── logger.py            # Logging configuration
│   │   ├── validators.py        # Data validation
│   │   └── helpers.py           # Helper functions
│   │
│   └── analysis/
│       ├── __init__.py
│       ├── statistics.py        # Generate statistics
│       ├── visualizations.py    # Create visualizations
│       └── export.py            # Export in different formats
│
├── data/
│   ├── raw/                     # Raw crawled data
│   │   ├── iclr_2024/
│   │   └── iclr_2023/
│   ├── processed/               # Cleaned/processed data
│   └── cache/                   # API response cache
│
├── outputs/
│   ├── reports/                 # Generated reports
│   ├── visualizations/          # Charts and graphs
│   └── exports/                 # Exported data
│
├── tests/
│   ├── __init__.py
│   ├── test_crawler.py
│   ├── test_parsers.py
│   └── test_storage.py
│
├── scripts/
│   ├── crawl_conference.py      # Main crawling script
│   ├── batch_crawl.py           # Batch crawl multiple years/venues
│   ├── update_data.py           # Update existing data
│   └── generate_report.py       # Generate analysis reports
│
├── notebooks/
│   ├── exploratory_analysis.ipynb
│   └── data_visualization.ipynb
│
├── logs/                        # Application logs
│
├── .env                         # Environment variables
├── .gitignore
├── requirements.txt
├── setup.py
├── README.md
└── Makefile                     # Common commands
```

## 🔄 Data Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA COLLECTION LAYER                     │
├─────────────────────────────────────────────────────────────┤
│  1. Configuration                                            │
│     ├─ Load venue configs (ICLR, NeurIPS, etc.)            │
│     ├─ Set API credentials (if needed)                      │
│     └─ Define crawling parameters                           │
│                                                              │
│  2. API Client Management                                    │
│     ├─ Initialize OpenReview client                         │
│     ├─ Handle API version detection                         │
│     └─ Implement rate limiting                              │
│                                                              │
│  3. Data Fetching                                           │
│     ├─ Get paper submissions                                │
│     ├─ Fetch reviews for each paper                         │
│     ├─ Collect comments & rebuttals                         │
│     └─ Get meta-reviews & decisions                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    DATA PROCESSING LAYER                     │
├─────────────────────────────────────────────────────────────┤
│  4. Data Parsing & Cleaning                                 │
│     ├─ Extract structured fields                            │
│     ├─ Handle different API formats (v1/v2)                │
│     ├─ Clean text content                                   │
│     └─ Validate data completeness                           │
│                                                              │
│  5. Data Enrichment                                         │
│     ├─ Calculate derived metrics (avg rating, etc.)        │
│     ├─ Extract keywords & topics                            │
│     ├─ Sentiment analysis on reviews (optional)            │
│     └─ Link related papers                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     DATA STORAGE LAYER                       │
├─────────────────────────────────────────────────────────────┤
│  6. Primary Storage                                          │
│     ├─ Raw JSON (complete data)                            │
│     ├─ CSV summaries (quick access)                        │
│     └─ Database (optional: PostgreSQL/MongoDB)             │
│                                                              │
│  7. Cache Management                                        │
│     ├─ Cache API responses                                  │
│     ├─ Prevent duplicate requests                           │
│     └─ Enable incremental updates                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    DATA ANALYSIS LAYER                       │
├─────────────────────────────────────────────────────────────┤
│  8. Analysis & Insights                                      │
│     ├─ Generate statistics                                  │
│     ├─ Trend analysis over years                           │
│     ├─ Review quality metrics                               │
│     └─ Acceptance rate analysis                             │
│                                                              │
│  9. Visualization                                           │
│     ├─ Rating distributions                                 │
│     ├─ Topic trends                                         │
│     ├─ Review length analysis                               │
│     └─ Author/institution statistics                        │
│                                                              │
│  10. Export & Reporting                                     │
│      ├─ Generate PDF reports                                │
│      ├─ Export to various formats                           │
│      └─ Create dashboards (optional)                        │
└─────────────────────────────────────────────────────────────┘
```

## 🧭 Pipeline Walkthrough

### Pipeline A — Data Collection
- **Configuration bootstrap**: `config/settings.py` loads `.env`, venue YAML, and CLI flags, then instantiates a `CrawlerConfig` dataclass with rate limits and attachment preferences.
- **Client factory**: `src/crawler/base_crawler.py` exposes `OpenReviewClientFactory`. It tries API v2 (`openreview.api.OpenReviewClient`) and falls back to v1. A shared `RateLimiter` (see `src/utils/rate_limiter.py`) throttles requests.
- **Submission discovery**: Venue-specific crawlers (for example `ICLRCrawler`) resolve invitations (`Submission`, `Blind_Submission`, `ARR` mirrors). The crawler yields `SubmissionRecord` objects and stores raw JSON to `data/raw/{venue}/{year}/submissions/{forum_id}.json`.
- **Artifact fetching**: For each forum ID, the crawler downloads attachments (`client.get_attachments` or direct `pdf_url`) to `data/raw/{venue}/{year}/papers/{forum_id}.pdf`. Retry logic and checksum validation live in `src/utils/helpers.py`.
- **Note aggregation**: `fetch_forum_notes` collects reviews, meta-reviews, comments, decisions, and authorship records. Each note is normalized into `ReviewRecord`, `DecisionRecord`, or `CommentRecord` dataclasses before entering the parsing stage.

### Pipeline B — Parsing & Normalization
- **Schema-aware parsers**: `src/parsers/paper_parser.py` and `review_parser.py` map raw OpenReview payloads to consistent internal schemas, handling v1/v2 differences (nested `value` fields, anonymized IDs, rating formats).
- **Validation**: `src/utils/validators.py` ensures required fields (title, abstract, decision) are present. Invalid entries are logged to `logs/validation.log` and moved to `data/cache/rejects/`.
- **Cleaning & NLP hooks**: Optional processors (keyword extraction, language cleaning, sentiment scoring) live in `src/parsers/enrichments/`. Results are appended to each record as enrichment metadata.
- **Serialization**: Parsed records are written to `data/processed/{venue}/{year}/papers.jsonl` and `reviews.jsonl`. Each line is one normalized JSON object for easy downstream consumption.

### Pipeline C — Storage & Distribution
- **Primary sinks**: `src/storage/file_storage.py` persists JSONL plus summary CSVs (`papers_summary.csv`, `reviews_long.csv`). `db_storage.py` optionally streams records into Postgres/Mongo collections with upserts on `forum_id`.
- **Cache & incremental updates**: `src/storage/cache.py` (to create) writes hash manifests (`.manifest`) so future runs skip unchanged submissions unless `--force` is used.
- **Export automation**: `src/analysis/export.py` produces derived tables (acceptance rates, rating histograms) and stores them under `outputs/exports/`. Exports are versioned by run timestamp.

### Pipeline D — Analysis & Reporting
- **Statistics**: `src/analysis/statistics.py` computes metrics (average rating, decision distribution, review length). Outputs feed dashboards or notebooks.
- **Visualizations**: `visualizations.py` leverages matplotlib/Altair to save figures into `outputs/visualizations/`.
- **Narrative reports**: `scripts/generate_report.py` assembles summaries (markdown/PDF) combining stats, key charts, and notable comments. A Pandoc/WeasyPrint step can convert to PDF if needed.

## 🗂️ Storage Layout & Naming Conventions
- Raw payloads mirror the exact OpenReview responses for auditability.
- Processed datasets use newline-delimited JSON for stream processing.
- Large binaries (PDFs) stay separated in `papers/` with SHA256 filenames to prevent collisions.
- Each pipeline run writes a metadata file (`run.json`) describing configuration, timestamps, and Git commit for reproducibility.

```
data/
└── raw/iclr_2025/
    ├── submissions/
    │   └── {forum_id}.json
    ├── notes/
    │   └── {forum_id}/
    │       ├── reviews/{note_id}.json
    │       ├── comments/{note_id}.json
    │       └── decisions/{note_id}.json
    └── papers/{forum_id}.pdf
└── processed/iclr_2025/
    ├── papers.jsonl
    ├── reviews.jsonl
    ├── comments.jsonl
    └── summary.csv
```

## ⚙️ Orchestration Suggestions
- Provide CLI entry points (Typer/Click) in `scripts/` to run a full crawl: `python -m scripts.crawl_conference --venue iclr --year 2025 --accepted-only`.
- Enable pipeline scheduling with a simple `Makefile` target or GitHub Action that triggers nightly crawls and pushes processed artifacts.
- Integrate `.env` with `config/settings.py`; document required keys (`OPENREVIEW_USERNAME`, `OPENREVIEW_PASSWORD`, `OPENREVIEW_RATE_LIMIT`).

## ✅ Next Steps
- Flesh out the empty `src/` modules according to the stubs above.
- Add unit tests in `tests/` to cover crawler fallbacks, parser normalization, and storage adapters.
- Document edge cases (e.g., withdrawn submissions, missing PDFs) in `docs/troubleshooting.md`.
## 🚀 Implementation Pipeline

### Phase 1: Core Infrastructure (Week 1-2)
1. Set up project structure
2. Implement base crawler class
3. Create configuration system
4. Add logging and error handling
5. Implement rate limiter

### Phase 2: Data Collection (Week 2-3)
1. Implement venue-specific crawlers
2. Add parser modules
3. Create caching mechanism
4. Build retry logic for failures
5. Add progress tracking

### Phase 3: Storage & Processing (Week 3-4)
1. Implement file storage
2. Add database support (optional)
3. Create data validation
4. Build incremental update system
5. Add data cleaning utilities

### Phase 4: Analysis & Visualization (Week 4-5)
1. Build statistics module
2. Create visualization tools
3. Implement export functions
4. Generate automated reports
5. Add data quality checks

### Phase 5: Testing & Documentation (Week 5-6)
1. Write unit tests
2. Integration testing
3. Create documentation
4. Add usage examples
5. Performance optimization

## 🔧 Key Features to Implement

### 1. **Rate Limiting**
- Respect API limits
- Exponential backoff on errors
- Configurable request delays

### 2. **Caching**
- Cache API responses
- Avoid re-fetching unchanged data
- Support incremental updates

### 3. **Error Handling**
- Retry failed requests
- Log all errors
- Resume from interruption

### 4. **Progress Tracking**
- Show progress bars
- Log checkpoint saves
- Estimate completion time

### 5. **Data Validation**
- Verify data completeness
- Check for missing fields
- Flag anomalies

### 6. **Flexible Configuration**
- YAML/JSON config files
- Environment variables
- Command-line arguments

### 7. **Monitoring & Logging**
- Structured logging
- Error notifications
- Performance metrics

## 📊 Data Models

### Paper Model
```python
{
    "id": str,
    "title": str,
    "abstract": str,
    "authors": List[str],
    "keywords": List[str],
    "venue": str,
    "year": int,
    "url": str,
    "reviews": List[Review],
    "decision": str,
    "metadata": dict
}
```

### Review Model
```python
{
    "id": str,
    "paper_id": str,
    "rating": float,
    "confidence": str,
    "summary": str,
    "strengths": str,
    "weaknesses": str,
    "questions": str,
    "timestamp": datetime
}
```

## 🎯 Usage Examples

### Basic Crawling
```bash
python scripts/crawl_conference.py --venue iclr --year 2024
```

### Batch Processing
```bash
python scripts/batch_crawl.py --venue iclr --years 2020-2024
```

### Generate Report
```bash
python scripts/generate_report.py --input data/raw/iclr_2024
```

### Update Existing Data
```bash
python scripts/update_data.py --venue iclr --year 2024 --mode incremental
```

## 🛡️ Best Practices

1. **Version Control**: Track all code changes, ignore data files
2. **Configuration Management**: Use environment variables for sensitive data
3. **Error Handling**: Always log errors with context
4. **Testing**: Write tests for critical components
5. **Documentation**: Keep README and docstrings updated
6. **Performance**: Use async/parallel processing for large datasets
7. **Data Privacy**: Respect author privacy, follow terms of service
8. **Reproducibility**: Version your data exports

## 📈 Scalability Considerations

1. **Database**: Migrate to PostgreSQL/MongoDB for large datasets
2. **Distributed Processing**: Use Celery for parallel crawling
3. **Cloud Storage**: Use S3/GCS for data storage
4. **API Management**: Implement request queuing
5. **Monitoring**: Add alerting for failures
6. **Caching**: Use Redis for distributed caching
