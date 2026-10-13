# Competitor Analysis AI Agent

A FastAPI-based backend that scrapes a company's website, analyzes it with Google Gemini (via LangChain), and streams competitive intelligence results over **Server-Sent Events (SSE)**. Output includes company profile, market analysis, market share estimate, competitor lists (local/national/global), detailed competitor comparisons, SWOT analysis, a comparison table, and surpass recommendations. Results are cached per (user, URL) in Supabase.

## Architecture

```
main.py                       FastAPI entry point (port 4545)
routes/extract.py             SSE extraction endpoint + analysis management endpoints
scraper/scraper.py            crawl4ai-based web crawling (site + competitor)
llm_processing/llm_processor.py      Gemini orchestration (all LLM calls)
llm_processing/prompt_templates.py   Prompt builders for every analysis step
schemas/company_schema.py     Pydantic models for inputs/outputs
utils/helper.py               Supabase helpers (upsert, exists, list, delete, JSONB cleaning)
utils/markdown_to_text.py     markdown -> plain-text sanitizer
utils/news_scraper.py         SerpAPI news snippets for market analysis
utils/serpapi_competitor_search.py   Optional SerpAPI competitor lookup
utils/supabase_client.py      Shared Supabase client
utils/logger.py               Logging setup
config/settings.py            Centralized env/config (single source of truth)
```

### Pipeline flow

1. `GET /api/extract` streams these SSE events in order:

| Event | Description |
|---|---|
| `status` | Progress updates (human-readable step) |
| `company_profile` | Extracted company profile |
| `market_data` | Market size / growth / regions / top players |
| `market_share` | Market capture estimate + growth recommendations |
| `local_competitors` / `national_competitors` / `global_competitors` | Generated competitor lists |
| `local_competitor_detailed_profile` | Per-competitor deep dive (5 local competitors) |
| `swot_analysis` | SWOT for our company and qualified competitors |
| `comparison_table` | Side-by-side comparison table |
| `surpass_recommendations` | Actionable strategies to surpass competitors |
| `process_close` | Stream finished; data persisted to Supabase |
| `error` | Any failure (also streams per-step) |

If an analysis already exists for the same `(url, user_id)` and `update` is not set, cached data is streamed back instead of re-running the pipeline.

## Setup

### 1. Environment variables

Copy `.env.example` to `.env` and fill in your values:

```
GEMINI_API_KEY="your-gemini-api-key"
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your-supabase-service-role-key"
SERPAPI_API_KEY="your-serpapi-key"
```

Optional: `GEMINI_MODEL` (default `gemini-2.0-flash`), `APP_PORT` (default `4545`).

> **Security:** the real `.env` is git-ignored. Never commit secrets.

### 2. Install

```bash
pip install -r requirements.txt
playwright install --with-deps   # downloads headless browsers used by crawl4ai
```

### 3. Required Supabase schema

- `public_users` table with at least an `id` column (used to validate `user_id`).
- `competitor_analysis` table with columns:
  - `id`, `link`, `user_id`, `created_at`, `company_name`, `category`
  - JSONB columns: `company_profile`, `market_data`, `market_capture`,
    `local_competitor`, `national_competitor`, `global_competitor`,
    `swot_analysis`, `comparison_table`, `surpass_recommendations`
  - Table should have a **unique constraint on `(user_id, link)`** for the upsert.

## Run

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 4545
```

Docker:

```bash
docker compose up --build -d
```

## API Endpoints

| Method | Path | Query params | Description |
|---|---|---|---|
| GET | `/` | – | Health check |
| GET | `/api/extract` | `url`, `user_id`, optional `update=true` | Full analysis, streamed via SSE |
| GET | `/api/analyses` | `user_id` | List saved analyses (summary) |
| GET | `/api/analysis` | `url`, `user_id` | Fetch a single saved analysis |
| DELETE | `/api/analysis` | `url`, `user_id` | Delete a saved analysis |

Use `update=true` to force a fresh extraction (existing record is replaced).

## Tests

```bash
pytest
```

Tests cover the pure logic (markdown sanitizing, JSONB preparation, schema validation) and do not require external services.