# Fishing Conditions Research Crew (CrewAI + Ollama)

Minimal, production-ready research pipeline that:
- Discovers location context (NOAA buoy + tide station)
- Gathers marine and weather data
- Optionally performs web search (if configured)
- Produces a clean Markdown report for anglers

## Features

- **Marine Weather Analysis**: NOAA data, tides, swell, wind patterns
- **Fishing Intelligence**: Current conditions, techniques, species behavior
- **Comprehensive Reports**: Detailed analysis with actionable recommendations
- **Seasickness Risk Assessment**: Data-driven safety analysis

## Quick Start

### Prerequisites

- Python 3.10+
- Ollama running locally (for LLM)

### Installation

1. Clone the repository:
```bash
git clone "https://github.com/rchow93/fishing-assistant"
cd fishing-assistant
```

2. Install dependencies:
```bash
pip install -e .
```

**Key Dependencies (see pyproject.toml):**
- `crewai>=0.157.0`
- `crewai-tools>=0.6.0`
- `python-dotenv>=1.0.1`
- `requests>=2.32.3`
- `pydantic>=2.9.2`
- `pyyaml>=6.0.1`
- `ollama>=0.3.0`
- `pandas>=2.2.3`
- `litellm>=1.70.0`

3. Configure LLM (minimal): already set to minimal syntax in code:
```python
        self.llm = LLM(
            model="ollama/qwen3:8b",
            base_url="http://localhost:11434"
        )

        self.llm2 = LLM(
            model="ollama/mistral-small3.2:24b",
            base_url="http://localhost:11434"
        )
```
These models worked well for this app but you can use any paid for LLM API's or other Ollama models. The key is that they can reason and tool call especially for websearch.

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your Ollama API key for web search functionality
# Get your free API key from: https://ollama.com/account
```

**Note:** Ollama is used for LLMs; Ollama web search is tool used for search but can be replaced by serper, tavily, or even firecrawl. (For using Ollama requires OLLAMA_API_KEY).

5. Start Ollama (if not already running):
```bash
ollama serve
```

### Usage

Preferred (console script defined in `pyproject.toml`):

```bash
fishing-assistant \
  --location "Half Moon Bay, CA" \
  --fish-species "rockfish" \
  --date "2025-11-02"
```

Alternative (module):

```bash
python -m fishing_assistant.main \
  --location "Half Moon Bay, CA" \
  --fish-species "rockfish" \
  --date "2025-11-02"
```

## Project Structure

```
fishing-assistant/
├── README.md
├── pyproject.toml
├── .env.example
├── reports/                     # Generated fishing reports
└── src/
    └── fishing_assistant/
        ├── __init__.py
        ├── crew.py              # Agents, tasks, crew assembly
        ├── main.py              # CLI entrypoint (console script)
        ├── config/
        │   ├── agents.yaml      # Agent definitions
        │   └── tasks.yaml       # Task definitions and output spec
        └── tools/
            ├── __init__.py
            └── custom_tool.py   # Weather/Marine/NOAA/Moon + Web Search + Scrape URL
```

## Models

Minimal LLM config used in code (swap to your models as desired):
```python
self.llm = LLM(
  model="ollama/qwen3:8b",
  base_url="http://localhost:11434"
)

self.llm2 = LLM(
  model="ollama/mistral-small3.2:24b",
  base_url="http://localhost:11434"
)
```
These work well for reasoning and tool use; you can swap to other Ollama or paid APIs.

## Configuration

### Agents

The system uses three specialized agents:

- **Marine Analyst**: Analyzes weather and marine conditions
- **Fishing Expert**: Researches fishing techniques and conditions
- **Report Writer**: Compiles comprehensive reports

### Tasks

Three main tasks orchestrate the research:

1. **Analyze Conditions**: Gather and analyze marine weather data
2. **Research Fishing**: Find current fishing conditions and techniques
3. **Write Report**: Compile everything into a comprehensive report

## Environment Variables

Create `.env` from `env.example`:
- `OLLAMA_API_KEY` (required for Web Search + Scrape flow)
- `OLLAMA_BASE_URL` (default: http://localhost:11434)

## Architecture & Flow

- **Agents**
  - **Marine Analyst**: Calls each data tool with a single JSON input (no batching). Uses: Weather Forecast, Marine Conditions API, NOAA Tide Predictions, NOAA Buoy Data, NOAA Weather Forecast, Moon Phase Data. Produces seasickness risk windows and an hourly view.
  - **Fishing Intelligence Researcher**: MUST use tools. First Web Search (Ollama web_search) to find recent sources, then Scrape URL to fetch content from 3–5 top URLs. No hallucinations. Cite source URLs used.
  - **Report Writer**: Compiles the final markdown report matching the required structure.

- **Tools** (inputs are single JSON objects):
  - Weather Forecast: {}
  - Marine Conditions API: {"date": "YYYY-MM-DD"}
  - NOAA Tide Predictions: {"date": "YYYY-MM-DD"}
  - NOAA Buoy Data: {"hours": 24}
  - NOAA Weather Forecast: {}
  - Moon Phase Data: {"date": "YYYY-MM-DD"}
  - Web Search (Ollama): {"query": "..."}
  - Scrape URL: {"url": "https://example.com/page"}

- **Task rules**
  - One tool per action; never batch a list of tool inputs.
  - Web Search → Scrape URL (3–5 pages) for fishing intelligence.

## Output

Reports are saved in `reports/` and the absolute path is printed. The final report matches this structure (like the previous “old app”):

- H1: Rockfish Fishing Report – {location} ({fishing_date_formatted})
- Executive Summary (date, location, species)
- Weather / Marine Conditions (NOAA + Buoy)
  - Table: Time (LT), Temp (°C), Wave Height (m), Wind (kt), Tide, Risk of Seasickness
- Fishing Intelligence
  - Bite Status (recent)
  - Prime Locations & Depths — Table: Area | Structure / Feature | Typical Depth (ft)
  - Bait Recommendations
  - Rigging & Tackle Specs — Table: Item | Recommended Specification
  - Fishing Techniques (bulleted)
  - Current Regulations (for location/species)
- Safety Tips & Practical Advice
- Quick Reference Table – Hourly Outlook — Table: Time, Temp (°C), Wind (kt), Wave Height (m), Tide, Seasickness Risk
- Sources Used — URLs from Web Search + Scrape URL (3–5 pages)

## Troubleshooting

- Web Search errors: ensure `OLLAMA_API_KEY` is in `.env`
- “File saved to” lines inside report: fixed via content normalization
- Report path: saved to `reports/` (not root)
- Multi-input tool calls: Marine Analyst now uses one tool per action (single JSON object)
- Console script not found: run `pip install -e .` to register `fishing-assistant`

## Privacy & Git Hygiene

- `.env` is ignored; do not commit secrets. Use `.env.example` for templates.
- Consider ignoring `reports/` if you don’t want to commit generated outputs.

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions, please open an issue on GitHub.