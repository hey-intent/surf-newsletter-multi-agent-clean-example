# Surf Newsletter Generator

An AI-powered surf newsletter generator that uses multi-agent orchestration with LangGraph to automatically curate the best surf news from across the web. Three distinct AI "editors" with unique personalities evaluate and rank articles according to their specialized criteria, ensuring diverse and comprehensive coverage.

## Overview

The Surf Newsletter Generator fetches surf-related articles from 11+ RSS sources and runs them through a sophisticated multi-agent pipeline. Each AI agent (Johnny, Annie, and Joana) brings their unique perspective to article selection, creating a balanced newsletter that covers performance, lifestyle, and environmental aspects of surfing.

## Key Features

- **Multi-Agent Orchestration**: Powered by LangGraph 1.0.6 with parallel execution using `Send()` API
- **Three Distinct Personas**: Each with unique evaluation criteria and personality
- **5-Phase Pipeline**: Sourcing, Selection, Cross-Grading, Final Ranking, and HTML Generation
- **11+ RSS Sources**: Coverage from Surfer Magazine, WSL, The Inertia, Stab, BeachGrit, and more
- **Parallel Processing**: Agents work concurrently for efficient evaluation
- **HTML Output**: Beautiful newsletters rendered with Jinja2 templates

## Architecture

The project follows a modular architecture organized in the `src/` directory:

```
src/
├── core/
│   ├── models.py           # Pydantic data models (Article, Grade, etc.)
│   ├── config.py           # RSS sources, pipeline config, LLM settings
│   ├── llm.py              # LLM client initialization
│   └── personas/
│       ├── base.py         # Base Persona class
│       ├── johnny.py       # Performance & competition editor
│       ├── annie.py        # Vibe & lifestyle editor
│       ├── joana.py        # Community & environment editor
│       └── __init__.py     # ALL_PERSONAS registry
├── agents/
│   ├── base.py             # Base agent functionality
│   ├── selector.py         # Article selection agent
│   └── grader.py           # Article grading agent
├── compute/
│   ├── fetcher.py          # RSS feed parsing and article fetching
│   ├── aggregator.py       # Results aggregation and ranking
│   └── renderer.py         # HTML newsletter generation
└── pipelines/
    ├── state.py            # LangGraph state definition
    ├── nodes.py            # Pipeline node implementations
    ├── graph.py            # LangGraph workflow definition
    └── orchestrator.py     # Pipeline execution coordinator
```

## The Three Personas

### 1. Johnny - Performance & Competition Focus

Former pro tour surfer with 15 years of competition experience. Obsessed with technical maneuvers, scores, and board design.

**Evaluation Criteria:**
- **Performance Level (30%)**: Technical quality, trick innovation
- **Competition Relevance (30%)**: WSL/CT/QS coverage, results, rankings
- **Equipment/Tech (20%)**: New gear, board science, R&D
- **Data/Stats (20%)**: Numbers, quantitative analysis, metrics

**Style**: Direct, technical, factual. Respects pure performance.

### 2. Annie - Vibe & Lifestyle Focus

Digital nomad and surf trip addict for 8 years. Travels the world searching for the best spots and perfect vibes.

**Evaluation Criteria:**
- **Destination Appeal (35%)**: Exotic spots, surf trips, paradise locations
- **Visual/Aesthetic (25%)**: Photo/video quality, visual inspiration
- **Lifestyle/Culture (25%)**: Surf art, music, fashion, food
- **Fun Factor (15%)**: Light-hearted, feel-good stories, emotions

**Style**: Enthusiastic, inspiring, focused on experience and emotions.

### 3. Joana - Community & Environment Focus

Environmental activist and committed surfer for 12 years. Believes in surfing as a vehicle for social and cultural change.

**Evaluation Criteria:**
- **Environmental Impact (35%)**: Ecology, ocean protection, sustainability
- **Community/Social (30%)**: Inclusivity, surf therapy, education
- **Cultural Diversity (20%)**: Surfing across different cultures
- **Activism/Awareness (15%)**: Social causes, raising awareness

**Style**: Engaged, conscious, focused on positive impact and change.

## Pipeline Architecture

The newsletter generation follows a 5-phase pipeline orchestrated by LangGraph:

```
                    ┌─────────────────────────────────────┐
                    │      PHASE 1: SOURCING              │
                    │  Fetch from 11+ RSS feeds           │
                    │  Deduplicate & filter by date       │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │   PHASE 2: SELECTION (Parallel)     │
                    │                                     │
            ┌───────┴────────┬─────────────┬──────────────┴───────┐
            │                │             │                      │
        ┌───▼────┐      ┌────▼───┐    ┌───▼────┐                │
        │ Johnny │      │ Annie  │    │ Joana  │                │
        │  Top 6 │      │ Top 6  │    │ Top 6  │                │
        └───┬────┘      └────┬───┘    └───┬────┘                │
            │                │             │                      │
            └────────────────┴─────────────┴──────────────────────┤
                                                                  │
                    ┌─────────────────────────────────────────────▼┐
                    │     AGGREGATE SELECTIONS                     │
                    │  Deduplicate → ~15-18 unique articles        │
                    └──────────────┬───────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────────────┐
                    │   PHASE 3: CROSS-GRADING (Parallel)         │
                    │  Each persona grades articles they didn't   │
                    │  select (only non-selectors grade)          │
                    └──────────────┬──────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────────────┐
                    │     AGGREGATE PHASE 3                       │
                    │  Rank by average score → Top 15 finalists   │
                    └──────────────┬──────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────────────┐
                    │   PHASE 4: FINAL GRADING (Parallel)         │
                    │  ALL personas grade ALL 15 finalists        │
                    │  (3 personas × 15 articles = 45 tasks)      │
                    └──────────────┬──────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────────────┐
                    │     AGGREGATE FINAL                         │
                    │  Final ranking by weighted average          │
                    └──────────────┬──────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────────────┐
                    │   PHASE 5: GENERATE                         │
                    │  Render HTML newsletter with Jinja2         │
                    └─────────────────────────────────────────────┘
```

### Parallel Execution with LangGraph Send()

The pipeline leverages LangGraph's `Send()` API for efficient parallel execution:

- **Phase 2**: All 3 personas select articles simultaneously
- **Phase 3**: Multiple grading tasks execute in parallel (one per persona-article pair)
- **Phase 4**: 45 grading tasks execute in parallel (3 personas × 15 finalists)

This parallelization significantly reduces total execution time compared to sequential processing.

## Tech Stack

- **Python**: 3.12+
- **LangGraph**: 1.0.6 (multi-agent orchestration with parallel execution)
- **LangChain**: 1.2.6 (LLM integration)
- **LangChain-OpenAI**: 1.1.7 (OpenAI-compatible API client)
- **Pydantic**: 2.12.5+ (data validation)
- **Jinja2**: 3.1.6+ (HTML templating)
- **feedparser**: 6.0.12+ (RSS parsing)
- **BeautifulSoup4**: 4.14.3+ (HTML parsing)
- **requests**: 2.32.5+ (HTTP client)
- **tenacity**: 9.0.0+ (retry logic)
- **python-dotenv**: 1.2.1+ (environment variable management)

## RSS Sources

The pipeline fetches articles from 11 curated surf media sources:

**General Surf Media:**
- Surfer Magazine
- Surfline News
- BeachGrit
- Stab Magazine

**Competition & Performance:**
- WSL (World Surf League)
- Surfing Magazine

**Culture & Lifestyle:**
- The Inertia
- Tracks Magazine
- Wavelength Magazine

**Regional:**
- Surf Europe
- Surf Session

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd surf-newsletter
```

2. Install dependencies:

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r pyproject.toml
```

3. Configure environment variables:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
# OPENROUTER_API_KEY=your_api_key_here
```

4. Get an OpenRouter API key:
   - Visit [https://openrouter.ai/keys](https://openrouter.ai/keys)
   - Create an account and generate an API key
   - Add it to your `.env` file

## Configuration

The pipeline uses OpenRouter by default with the `mistralai/mistral-small-3.2-24b-instruct` model. You can customize this in `src/core/config.py`:

```python
# LLM configuration
LLM_MODEL = "mistralai/mistral-small-3.2-24b-instruct"
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 2000
LLM_BASE_URL = "https://openrouter.ai/api/v1"
```

### Pipeline Configuration

Adjust pipeline behavior in `src/core/config.py`:

```python
# Pipeline configuration
MIN_ARTICLES = 50          # Minimum articles to fetch
MAX_ARTICLES = 100         # Maximum articles to process
ARTICLES_PER_AGENT = 6     # Articles each persona selects
FINALISTS_COUNT = 8        # Final articles in newsletter
```

## Usage

### Basic Usage

Generate a newsletter with default settings (7 days lookback):

```bash
python main.py
```

### Advanced Options

```bash
# Look back 3 days instead of 7
python main.py --days 3

# Specify custom output filename
python main.py --output my_newsletter.html

# Enable debug logging
python main.py --debug

# Combine options
python main.py --days 5 --output weekly_surf.html --debug
```

### Command-Line Arguments

- `--days N`: Number of days to look back for articles (default: 7)
- `--min-articles N`: Minimum number of articles to fetch (default: 50)
- `--output PATH`: Output HTML filename (default: `newsletter_YYYYMMDD.html`)
- `--debug`: Enable debug logging for detailed execution traces

### LangGraph Dev Server

For an interactive development experience with hot reloading and a visual interface, you can run the LangGraph development server:

```bash
# Install dev dependencies (includes langgraph-cli)
uv sync --extra dev

# Start the dev server
langgraph dev
```

The server starts at `http://127.0.0.1:2024` and provides:
- **REST API**: Invoke the graph programmatically
- **LangGraph Studio**: Visual graph debugging (opens automatically in browser)
- **Hot Reloading**: Changes to your code are picked up automatically
- **State Persistence**: Local state storage for debugging

#### API Usage Example

Once the server is running, you can invoke the newsletter pipeline via HTTP:

```bash
# Start a new newsletter generation run
curl -X POST http://127.0.0.1:2024/runs \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "newsletter",
    "input": {
      "days": 7
    }
  }'
```

#### Configuration

The server uses `langgraph.json` which maps the graph name to its Python module:

```json
{
  "graphs": {
    "newsletter": "./src/pipelines/newsletter_graph.py:newsletter_graph"
  },
  "env": ".env"
}
```

### Output

The pipeline generates an HTML newsletter file (e.g., `newsletter_20260117.html`) containing:

- Top-ranked articles with scores and persona commentary
- Article metadata (source, date, excerpt)
- Visual layout with images
- Links to original articles

## Adding a New Persona

To add a fourth persona to the editorial panel:

1. **Create a new persona file** in `src/core/personas/`:

```python
# src/core/personas/carlos.py
from src.core.personas.base import Persona

CARLOS = Persona(
    name="Carlos",
    description=(
        "Big wave charger with 20 years experience in heavy water. "
        "Focuses on extreme conditions and safety."
    ),
    system_prompt="""You are Carlos, a big wave specialist.
You evaluate articles based on:
- Wave size and power
- Safety and preparation
- Big wave locations and conditions
- Risk management and expertise

Style: Serious, safety-conscious, respects the ocean's power.""",
    criteria_text="""- Wave Power (40%): Size, intensity, danger level
- Safety/Preparation (30%): Equipment, training, risk management
- Location Quality (20%): World-class big wave spots
- Expertise Required (10%): Skill level, experience needed""",
)
```

2. **Register the persona** in `src/core/personas/__init__.py`:

```python
from src.core.personas.carlos import CARLOS

ALL_PERSONAS = [JOHNNY, ANNIE, JOANA, CARLOS]

__all__ = [
    "Persona",
    "JOHNNY",
    "ANNIE",
    "JOANA",
    "CARLOS",
    "ALL_PERSONAS",
]
```

3. **Run the pipeline** - LangGraph will automatically include the new persona in all phases.

The pipeline dynamically adapts to the number of personas in `ALL_PERSONAS`, so no changes to the graph logic are required.

## Development

### Project Structure

- `main.py`: CLI entry point
- `src/core/`: Core models, configuration, and personas
- `src/agents/`: Agent implementations (selector, grader)
- `src/compute/`: Data processing (fetcher, aggregator, renderer)
- `src/pipelines/`: LangGraph orchestration
- `templates/`: Jinja2 HTML templates

### Logging

The pipeline uses Python's built-in `logging` module:

- **INFO**: Default level, shows phase progression and key metrics
- **DEBUG**: Detailed execution traces, LLM calls, grading decisions

Enable debug mode with the `--debug` flag for troubleshooting.

### Testing

To test the pipeline with a small dataset:

```bash
python main.py --days 1 --debug
```

This fetches only the most recent articles and provides detailed logging.

## How It Works

### Phase 1: Sourcing

The `fetcher.py` module:
1. Fetches articles from 11 RSS feeds
2. Parses publication dates and filters by time window (default: 7 days)
3. Extracts title, URL, excerpt, source, and image
4. Deduplicates by URL and normalized title
5. Sorts by date (newest first)
6. Caps at MAX_ARTICLES (default: 100)

### Phase 2: Selection

Each persona independently:
1. Receives the full article list
2. Evaluates articles against their criteria
3. Selects their top 6 articles
4. Provides reasoning for each selection

**Parallelization**: All 3 personas run simultaneously via LangGraph `Send()`.

**Aggregation**: Selected articles are deduplicated (typically ~15-18 unique articles from 18 total selections).

### Phase 3: Cross-Grading

For each selected article:
1. Only personas who DIDN'T select it provide grades
2. Each grader assigns a score (0-100) with reasoning
3. This prevents self-selection bias

**Parallelization**: Multiple grading tasks run concurrently.

**Aggregation**: Articles are ranked by average cross-grade score. Top 15 become finalists.

### Phase 4: Final Grading

ALL personas grade ALL 15 finalists:
1. Each of 3 personas grades all 15 articles (45 grading tasks)
2. Scores include both original selections and new evaluations
3. Final ranking uses weighted average across all grades

**Parallelization**: All 45 grading tasks execute concurrently for maximum efficiency.

### Phase 5: Generate

The `renderer.py` module:
1. Renders HTML using Jinja2 templates
2. Includes article metadata, scores, and persona commentary
3. Adds visual elements (images, source badges, dates)
4. Writes to output file

## Troubleshooting

### No API Key Error

```
Error: OPENROUTER_API_KEY not found in environment
```

**Solution**: Ensure `.env` file exists with a valid API key:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

### Insufficient Articles

```
Warning: Only X articles from RSS, running web search (need 50)
```

**Solution**: Either:
- Increase the `--days` parameter to look further back
- Implement the web search fallback in `fetcher.py` (currently a placeholder)
- Reduce `MIN_ARTICLES` in `config.py`

### Rate Limiting

If you encounter rate limits from OpenRouter:
- Add delays between API calls
- Use a model with higher rate limits
- Implement retry logic with exponential backoff (already included via `tenacity`)

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph) for multi-agent orchestration
- Powered by [OpenRouter](https://openrouter.ai/) for LLM access
- RSS feeds provided by the surf media community

---

**Generated with AI-powered multi-agent orchestration** - Bringing diverse perspectives to surf news curation.
