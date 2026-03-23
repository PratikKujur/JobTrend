# Job Market Intelligence

A full-stack application for scraping, processing, and analyzing job market data from LinkedIn. Features a web scraper, REST API, and interactive dashboard.

## Features

- **LinkedIn Job Scraper**: Automated scraping of job listings using Selenium
- **Data Processing**: Clean and transform raw job data with skill extraction
- **SQLite Database**: Store and query job data efficiently
- **REST API**: FastAPI-powered API for accessing job market data
- **Interactive Dashboard**: Streamlit dashboard with visualizations for:
  - Top in-demand skills
  - Location distribution
  - Experience level distribution
  - Job trends and statistics

## Project Structure

```
JobTrend/
├── api/              # FastAPI REST API
├── dashboard/        # Streamlit dashboard
├── database/         # SQLite models and queries
├── processing/       # Data processing pipeline
├── scraper/          # LinkedIn scraper
├── utils/            # Helper functions
├── data/             # Data storage (JSON, CSV, SQLite)
└── main.py           # CLI entry point
```

## Requirements

- Python 3.11+
- Chrome browser (for scraper)

## Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run Full Pipeline (Process + Database)

```bash
python main.py pipeline
```

### Run Individual Components

```bash
python main.py scrape     # Run scraper (requires LinkedIn credentials)
python main.py process    # Process raw data
python main.py db         # Load data to database
python main.py api        # Start API server
python main.py dashboard  # Start dashboard
```

### Or run services directly

**API Server** (port 8000):
```bash
uvicorn api.main:app --reload
```

**Dashboard** (port 8501):
```bash
streamlit run dashboard/app.py
```

## API Endpoints

- `GET /jobs` - List all jobs (supports filters)
- `GET /skills/top` - Get top skills by demand
- `GET /locations` - Location statistics
- `GET /experience` - Experience level distribution
- `GET /stats` - Summary statistics

## Dashboard Features

- Summary statistics cards
- Top skills bar chart
- Jobs by location pie chart
- Experience level distribution
- Filterable job listings table
- Job detail expansion

## Notes

- The scraper requires LinkedIn credentials and Chrome browser
- Sample data is included in `data/raw_jobs.json` for demonstration
- The API must be running before the dashboard can display data