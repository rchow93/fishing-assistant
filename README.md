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
Medium-Article/
├── README.md
├── pyproject.toml
├── .env.example
├── reports/                     # Generated fishing reports
└── src/
    └── fishing_assistant/
        ├── __init__.py
        ├── crew.py              # Main crew definition
        ├── main.py              # Entry point
        ├── config/
        │   ├── agents.yaml       # Agent configurations
        │   └── tasks.yaml        # Task definitions
        └── tools/
            ├── __init__.py
            └── custom_tool.py    # Custom tools and utilities
```

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

## Output

The system generates a Markdown report in the `reports/` directory at the project root (and prints the absolute path). The report includes:

- Marine weather conditions
- Tide analysis and timing
- Swell and wind conditions
- Moon phase information
- Seasickness risk assessment
- Fishing recommendations
- Best fishing times
- Species-specific techniques

## Troubleshooting

- LiteLLM fallback: ensure minimal LLM syntax or `pip install litellm`
- Config not found: `pip install -e .` and verify MANIFEST/package-data
- CrewBase pattern: call `.crew().kickoff()`

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