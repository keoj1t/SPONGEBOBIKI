# Claude Growth Intelligence

**HackNU — Growth Engineering Track**

Social media intelligence system that tracks Claude AI mentions, sentiment, and engagement trends across 7 platforms.

---

## Key Findings

- **YouTube is the engagement engine** — 12% of posts drive 68% of total engagement
- **Reddit is the discussion engine** — 83% of volume, organic UGC drives discovery
- **"Switching from ChatGPT" is the strongest narrative** — 4,319 avg engagement
- **Claude grows through earned media** — zero official posts in top 50; growth is product-led
- **Visual content outperforms text 5-10x** — carousel and video formats dominate

**Dataset:** ~1,900 posts across 7 platforms with sentiment analysis, keyword tracking, narrative bucketing, time-series trends, TF-IDF topic discovery, and anomaly detection.

---

## Project Structure

```
├── run.py                  # main entry point
├── requirements.txt
├── Dockerfile
├── .gitignore
│
├── core/                   # shared utilities
│   ├── config.py           # paths, keywords, thresholds
│   ├── log.py              # dual-output logging (console + file)
│   └── wrapper.py          # scraper subprocess orchestration
│
├── pipeline/               # data processing & analysis
│   ├── merge.py            # clean, filter English, deduplicate
│   ├── data_quality.py     # validation & fixes
│   ├── sentiment.py        # VADER sentiment scoring
│   ├── analyze.py          # descriptive analytics + charts
│   ├── timeseries.py       # weekly trends with trendlines
│   ├── topics.py           # TF-IDF + emerging keyword detection
│   ├── alerts.py           # anomaly detection (spikes, viral, trending)
│   ├── report.py           # auto-generated markdown report
│   └── scheduler.py        # APScheduler recurring runs
│
├── scrapers/               # per-platform data collectors
│   ├── reddit.py           # public JSON API (no key needed)
│   ├── youtube.py          # native search + page scraping (no key needed)
│   ├── tiktok.py           # Apify cloud actor
│   ├── twitter.py          # Apify cloud actor
│   ├── instagram.py        # Apify cloud actor
│   ├── linkedin.py         # Apify cloud actor
│   ├── threads.py          # Apify cloud actor
│   └── search_engine.py    # free web search fallback (DDG/Bing/Google)
│
├── app/
│   └── dashboard.py        # Streamlit interactive dashboard
│
├── data/
│   ├── raw/                # per-platform CSVs from scrapers
│   └── final/              # merged dataset
│
├── output/
│   ├── reports/            # analysis CSVs, quality JSON, auto_report.md
│   ├── charts/             # matplotlib PNGs
│   ├── alerts/             # alerts.json + summary
│   └── logs/               # pipeline.log
│
└── tests/
    └── test_pipeline.py
```

---

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

**Environment variables** (create a `.env` file):

```bash
APIFY_TOKEN=your_apify_token
APIFY_TOKEN_TWITTER=your_twitter_token
APIFY_TOKEN_INSTAGRAM=your_instagram_token
APIFY_TOKEN_LINKEDIN=your_linkedin_token
APIFY_TOKEN_THREADS=your_threads_token
```

> Reddit and YouTube require **no API keys**. TikTok, Twitter, Instagram, LinkedIn, and Threads use Apify cloud actors. Without tokens, those scrapers produce empty CSVs — the pipeline still runs on available data.

**Docker alternative:**

```bash
docker build -t claude-growth .
docker run -p 8501:8501 --env-file .env claude-growth
```

---

## Usage

**Full pipeline** (scrape → merge → analyze → report):

```bash
python run.py
```

**Skip scraping**, reuse existing CSVs:

```bash
python run.py --skip-scrape
```

**Append mode** (incremental, deduplicates against existing data):

```bash
python run.py --skip-scrape --append
```

**Launch dashboard:**

```bash
streamlit run app/dashboard.py
```

---

## Pipeline Architecture

```
Scrapers → Raw CSVs → Merge & Deduplicate → Data Quality Check
  → Sentiment (VADER) → Descriptive Analytics → Time-Series Trends
  → TF-IDF Topics → Alert Detection → Markdown Report → Dashboard
```

Each step is an independent module in `pipeline/`. If a step fails, the rest continue. The entry point `run.py` orchestrates them sequentially with per-step error handling.

---

## Platforms

| Platform | Method | API Key? | Notes |
|----------|--------|:--------:|-------|
| Reddit | Public JSON API | No | Pagination, nested comments |
| YouTube | Native search + page scraping | No | HTML metric extraction |
| TikTok | Apify (`clockworks/tiktok-scraper`) | Yes | Cloud actor |
| Twitter | Apify (`altimis/scweet`) | Yes | Advanced search query |
| Instagram | Apify (`instagram-hashtag-scraper`) | Yes | Hashtag-based search |
| LinkedIn | Apify (`linkedin-posts-search`) | Yes | No-cookie scraper, engagement may be limited |
| Threads | Apify (`search-threads-by-keywords`) | Yes | Keyword-based search |

---

## Configuration

All paths, keywords, thresholds, and narrative patterns are centralized in `core/config.py`:

- **Keywords**: 30 tracked terms (switch, chatgpt, code, etc.)
- **Narrative buckets**: 6 regex patterns (comparison, switching, coding_dev, etc.)
- **Alert thresholds**: engagement spike 3σ, mention spike 2.5σ, viral 50× median

---

## Outputs

| Output | Location |
|--------|----------|
| Merged dataset | `data/final/final_dataset_eng.csv` |
| Analysis CSVs | `output/reports/*.csv` |
| Auto report | `output/reports/auto_report.md` |
| Charts | `output/charts/*.png` |
| Alerts | `output/alerts/alerts.json` |
| Pipeline log | `output/logs/pipeline.log` |

---

## Testing

```bash
pytest tests/ -v
```

Tests cover merge deduplication, date parsing, sentiment scoring, alert detection, and search engine imports.

---

## Limitations

- **LinkedIn engagement**: no-cookie scraper may return zero metrics
- **English only**: non-English content filtered via langdetect
- **Batch mode**: no real-time streaming; scheduler supports recurring runs
- **Dataset backups**: auto-created before each run (last 5 kept in `data/final/backups/`)


