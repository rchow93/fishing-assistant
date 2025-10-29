"""
Fishing Conditions Research Crew
Uses CrewAI @CrewBase pattern for clean, maintainable structure
"""

import os
from pathlib import Path
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import ScrapeWebsiteTool
from .tools import get_tools, get_search_tools
from dotenv import load_dotenv

# Resolve absolute paths to YAMLs bundled inside the package
_PKG_DIR = Path(__file__).resolve().parent
_CONFIG_DIR = _PKG_DIR / "config"

# =============================================================================
# LLM CONFIGURATION - EASY TO MODIFY!
# =============================================================================
# Dual LLM setup: Manager uses reasoning-enabled model, Workers use faster model
# Load environment early so provider configuration is available
load_dotenv()

#

# Alternative configurations (uncomment to use):
# MANAGER_MODEL = "ollama/qwen2.5:14b"  # Alternative powerful model
# WORKER_MODEL = "ollama/qwen2.5:7b"   # Alternative worker model
# MANAGER_MODEL = "gpt-4o"             # OpenAI manager (requires API key)
# WORKER_MODEL = "gpt-4o-mini"         # OpenAI worker (requires API key)
# MANAGER_BASE_URL = "https://api.openai.com/v1"  # OpenAI endpoint


@CrewBase
class FishingConditionsCrew:
    """
    Fishing research crew with 3 specialized agents:
    1. Marine Analyst - Gathers weather/ocean data, assesses seasickness risk
    2. Fishing Expert - Researches species-specific fishing intel
    3. Report Writer - Creates comprehensive trip report
    """
    
    agents_config = str(_CONFIG_DIR / "agents.yaml")
    tasks_config = str(_CONFIG_DIR / "tasks.yaml")
    
    def __init__(self, location_config: dict, fish_species: str = "rockfish"):
        """
        Initialize crew with location data and target species
        
        Args:
            location_config: Dict from FishingLocationDiscovery with lat/lon/stations
            fish_species: Target fish species for research
        """
        self.location_config = location_config
        self.fish_species = fish_species
        
        # Get data tools based on location
        self.data_tools = get_tools(location_config)
        
        # Search tools for fishing research
        self.search_tools = get_search_tools()
        
        # Note: File saving is handled in main.py, not via FileWriterTool
        # This prevents duplicate writes and path confusion
        
        self.llm = LLM(
            model="ollama/qwen3:8b",
            base_url="http://localhost:11434"
        )

        self.llm2 = LLM(
            model="ollama/mistral-small3.2:24b",
            base_url="http://localhost:11434"
        )
       
    
    @agent
    def marine_analyst(self) -> Agent:
        """Marine weather specialist with access to all data APIs"""
        return Agent(
            config=self.agents_config['marine_analyst'],
            tools=self.data_tools,
            max_iter=15,
            llm=self.llm2,
            reasoning=True,
            max_reasoning_attempts=5,
            verbose=True
        )
    
    @agent
    def fishing_expert(self) -> Agent:
        """Fishing intelligence researcher with web search"""
        return Agent(
            config=self.agents_config['fishing_expert'],
            tools=self.search_tools,
            max_iter=20,  # Matches original: max_iter=20
            reasoning=True,
            max_reasoning_attempts=3,
            llm=self.llm,
            verbose=True
        )
    
    @agent
    def report_writer(self) -> Agent:
        """Report writer that creates comprehensive fishing report (file saving handled by main.py)"""
        return Agent(
            config=self.agents_config['report_writer'],
            tools=[],  # No file tool - we save in main.py to control path/name
            llm=self.llm,
            max_iter=10,
            verbose=True
        )
    
    @task
    def analyze_conditions_task(self) -> Task:
        """Gather and analyze all weather/marine conditions"""
        return Task(
            config=self.tasks_config["analyze_conditions_task"],
            agent=self.marine_analyst(),
        )
    
    @task
    def research_fishing_task(self) -> Task:
        """Research species-specific fishing intelligence"""
        return Task(
            config=self.tasks_config["research_fishing_task"],
            agent=self.fishing_expert(),
        )
    
    @task
    def write_report_task(self) -> Task:
        """Create comprehensive fishing report"""
        return Task(
            config=self.tasks_config["write_report_task"],
            agent=self.report_writer(),
        )
    
    @crew
    def crew(self) -> Crew:
        """Assemble the crew with sequential task processing"""
        return Crew(
            agents=self.agents,  # Auto-populated by @CrewBase
            tasks=self.tasks,    # Auto-populated by @CrewBase
            process=Process.sequential,
            verbose=True
        )
