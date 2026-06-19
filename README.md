# CryptoPulse AI

CryptoPulse AI is a small creator-intelligence system for the AI Engineer assignment. It
collects recent crypto content, ranks it using engagement and freshness, identifies viral
patterns, and generates:

- 5 Instagram Reel ideas
- 3 YouTube video ideas
- 3 Twitter thread ideas
- Hooks, topics, angles, source links, and short script outlines

The application uses Claude when an Anthropic API key is configured. Live Research never
mixes bundled examples into its results. Demo Data is a separate, visibly labelled offline mode.

## Architecture

```text
YouTube API ───┐
Hacker News ───┤
CoinGecko ─────┼─> Normalize ─> Viral scoring ─> Claude analysis ─> Content ideas
Crypto RSS ────┤
Reddit* ───────┘

* Reddit is optional while official Data API approval is pending.
```

The system treats collected text as untrusted evidence and asks Claude for JSON-only output.
Generated ideas must use evidence URLs from the collected dataset.

## Technology

- Python 3.10+
- Streamlit
- Anthropic Python SDK
- YouTube Data API v3
- Hacker News public search
- CoinGecko Demo API
- Crypto RSS feeds
- Optional Reddit integration
- Pandas and Plotly
- Pytest

## Quick start

### Option A: uv

```bash
cd crypto-pulse-ai
cp .env.example .env
uv sync --extra dev
uv run streamlit run app.py
```

### Option B: virtual environment

```bash
cd crypto-pulse-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Open <http://localhost:8501>.

## API keys

Edit `.env`:

```dotenv
ANTHROPIC_API_KEY=your_key
ANTHROPIC_MODEL=claude-sonnet-4-6
YOUTUBE_API_KEY=your_google_api_key
COINGECKO_DEMO_API_KEY=your_coingecko_key
```

`ANTHROPIC_API_KEY` enables Claude-powered pattern analysis and generation.
`YOUTUBE_API_KEY` enables live YouTube search and statistics. `COINGECKO_DEMO_API_KEY`
enables authenticated access to trending coins and categories. Both are optional in Demo Data
mode.

To create a YouTube key:

1. Open Google Cloud Console.
2. Create or select a project.
3. Enable YouTube Data API v3.
4. Create an API key under Credentials.
5. Restrict the key to the YouTube Data API before sharing or deploying it.

## How the scoring works

The scorer first calculates platform-specific momentum:

```text
engagement = likes + comments*2 + shares*3
velocity = engagement / age_in_hours
score = log(views+1) + log(engagement+1) + log(velocity+1)
```

Reddit comments receive extra weight because discussion depth is a strong signal for
controversial and educational content.

Scores are then normalized within each platform to `0-100`. News is capped at `55` because
RSS feeds provide freshness but no social engagement. CoinGecko is capped at `75` because it
provides trend position rather than likes or comments. This prevents YouTube view counts from
overpowering every other source.

## Demo flow

1. Enter `crypto`, `stablecoins`, `Bitcoin regulation`, or another narrative.
2. Select Reddit, YouTube, and News.
3. Select **Live Research** for real APIs and feeds, or **Demo Data** for offline evaluation.
4. Click **Generate content intelligence**.
5. Show:
   - source counts and viral scores;
   - top engagement chart;
   - detected hooks and storytelling structures;
   - all 11 required ideas;
   - evidence links and downloadable JSON.

## Testing

```bash
pytest
ruff check .
```

The tests verify scoring behavior, JSON extraction, exact content-idea counts, and offline
pipeline operation.

## Important design decisions

- X/Twitter is not used as a collection source. The system still generates the three Twitter
  thread ideas required by the assignment.
- Live Research never silently inserts sample evidence.
- Demo Data is separate and clearly labelled.
- News has no social engagement metrics, so it receives a lower scoring weight and provides
  context rather than claiming virality.
- CoinGecko contributes current trending assets and categories, not social engagement.
- Hacker News contributes points and comment counts for technical crypto discussions.
- The LLM cannot invent evidence URLs: prompts explicitly restrict URLs to the supplied data.
- The output avoids investment recommendations and guaranteed price predictions.

## Production improvements

- Instagram and TikTok approved APIs
- Transcript and comment analysis for YouTube
- Database persistence and scheduled collection
- Deduplication using embeddings
- Engagement normalization by channel size
- Human feedback and content-performance tracking
- Background jobs, authentication, observability, and cost controls

## Suggested 3-5 minute demo

1. **Problem (30 sec):** creators manually scan many platforms.
2. **Architecture (45 sec):** collection, normalization, scoring, Claude, generation.
3. **Live run (90 sec):** run a topic and show ranked evidence.
4. **AI output (60 sec):** patterns and the 11 required ideas.
5. **Engineering choices (45 sec):** live/demo separation, evidence links, exact JSON
   validation, tests.
6. **Future scope (30 sec):** official social APIs, scheduling, and feedback loops.
