#!/usr/bin/env python3
"""
Fishing Assistant Research Crew
Main entry point for the fishing conditions research system
"""

import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

from fishing_assistant.crew import FishingConditionsCrew
from fishing_assistant.tools.location_discovery import FishingLocationDiscovery


def main():
    """Main entry point for the fishing research crew"""
    
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fishing Conditions Research Crew")
    parser.add_argument("--location", "-l", required=True, help="Fishing location (e.g., 'Half Moon Bay, CA')")
    parser.add_argument("--fish-species", "-f", default="rockfish", help="Target fish species (default: rockfish)")
    parser.add_argument("--date", "-d", help="Fishing date (YYYY-MM-DD format, default: tomorrow)")
    
    args = parser.parse_args()
    
    # Set fishing date
    if args.date:
        fishing_date = args.date
    else:
        fishing_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Get day of week and formatted date header
    fishing_datetime = datetime.strptime(fishing_date, "%Y-%m-%d")
    day_of_week = fishing_datetime.strftime("%A")
    fishing_date_formatted = fishing_datetime.strftime("%A, %B %d, %Y")
    
    print(f"🎣 FISHING CONDITIONS RESEARCH")
    print(f"📍 Location: {args.location}")
    print(f"🐟 Species: {args.fish_species}")
    print(f"📅 Date: {fishing_date} ({day_of_week})")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Discover location configuration
        print("\n🔍 Discovering location configuration...")
        location_discovery = FishingLocationDiscovery(location_name=args.location)
        location_discovery.discover_all()  # Run discovery
        location_config = location_discovery.get_config_dict()  # Get proper config format
        
        # Initialize the crew with location config
        crew = FishingConditionsCrew(
            location_config=location_config,
            fish_species=args.fish_species
        )
        
        # Run the crew with parameters (CrewBase pattern: call .crew() first)
        result = crew.crew().kickoff(
            inputs={
                "location": args.location,
                "fish_species": args.fish_species,
                "fishing_date": fishing_date,
                "day_of_week": day_of_week,
                "fishing_date_formatted": fishing_date_formatted
            }
        )
        
        # Persist report to a Markdown file in reports/ directory
        # Find project root (Medium-Article directory) by going up from src/fishing_assistant/main.py
        # __file__ is src/fishing_assistant/main.py, so go up 3 levels to get Medium-Article/
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent
        
        # Verify we're in the right place (check for pyproject.toml or src/ directory)
        if not (project_root / "pyproject.toml").exists() and not (project_root / "src").exists():
            # Fallback: try to find from current working directory
            cwd = Path.cwd()
            if (cwd / "pyproject.toml").exists():
                project_root = cwd
            elif (cwd / "Medium-Article" / "pyproject.toml").exists():
                project_root = cwd / "Medium-Article"
        
        reports_dir = project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        filename = f"fishing_report_{fishing_date.replace('-', '_')}.md"
        filepath = reports_dir / filename
        
        try:
            # Best-effort stringify
            content = result if isinstance(result, str) else str(result)
            # Normalize content: remove ANY file path/footer references and stray backticks
            lines = []
            for ln in content.splitlines():
                ln_lower = ln.strip().lower()
                # Remove any lines mentioning file paths or saving
                if any(phrase in ln_lower for phrase in [
                    'file saved to', 'file written', 'saved to', 'written to',
                    'file saved at', 'file written at'
                ]):
                    continue
                # Remove lines that look like absolute paths (start with /)
                if ln.strip().startswith('/') and ('report' in ln_lower or 'monterey' in ln_lower or 'txt' in ln_lower or 'md' in ln_lower):
                    continue
                lines.append(ln)
            
            # Remove trailing empty lines and backticks
            while lines and lines[-1].strip().strip('`') == "":
                lines.pop()
            
            content = "\n".join(lines).rstrip() + "\n"
            filepath.write_text(content, encoding='utf-8')
            saved_path = str(filepath.resolve())
        except Exception as e:
            print(f"⚠️ Warning: Could not save report file: {e}")
            saved_path = str(filepath.resolve())

        print("\n" + "=" * 60)
        print("✅ RESEARCH COMPLETED SUCCESSFULLY!")
        print(f"📄 Report saved to: {saved_path}")
        print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return saved_path
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("Please check your configuration and try again.")
        return None


if __name__ == "__main__":
    main()
