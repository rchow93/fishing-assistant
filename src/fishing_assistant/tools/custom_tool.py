"""
Fishing Data Tools - FIXED VERSION
Following CrewAI documentation for proper tool implementation
"""

import os
import requests
import pandas as pd
from datetime import datetime
from crewai.tools import BaseTool
from crewai_tools import ScrapeWebsiteTool
from pydantic import BaseModel, Field
from typing import Type
import os
import requests
import ollama
from dotenv import load_dotenv

# Ensure env is loaded so API keys are available
load_dotenv()

# Ollama web search requires OLLAMA_API_KEY in env
api_key = os.getenv('OLLAMA_API_KEY')
if not api_key:
    raise ValueError("OLLAMA_API_KEY not found in environment")


class WeatherInput(BaseModel):
    """Input schema for weather tool."""
    pass  # No inputs needed, uses instance data

class MarineInput(BaseModel):
    """Input schema for marine tool."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")

class BuoyInput(BaseModel):
    """Input schema for buoy tool."""
    hours: int = Field(24, description="Number of hours of data to retrieve")

class TidesInput(BaseModel):
    """Input schema for tides tool."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")

class NOAAWeatherInput(BaseModel):
    """Input schema for NOAA weather tool."""
    pass  # No inputs needed, uses instance data

class MoonInput(BaseModel):
    """Input schema for moon tool."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")

class WebSearchInput(BaseModel):
    """Input schema for web search tool."""
    query: str = Field(..., description="Search query text")

class ScrapeURLInput(BaseModel):
    """Input schema for scrape url tool."""
    url: str = Field(..., description="Website URL to scrape")


class WeatherTool(BaseTool):
    """Open-Meteo API for comprehensive weather data (FREE - no API key required)"""
    name: str = "Weather Forecast"
    description: str = "Get comprehensive weather including temperature, humidity, precipitation, wind, and detailed forecasts using Open-Meteo API (free)"
    args_schema: Type[BaseModel] = WeatherInput
    # Pydantic-managed fields (required for CrewAI BaseTool)
    lat: float
    lon: float
    
    def __init__(self, lat: float, lon: float):
        # Provide fields to BaseTool (Pydantic) for validation
        super().__init__(lat=float(lat), lon=float(lon))
        # Ensure attributes exist on the instance
        object.__setattr__(self, "lat", float(lat))
        object.__setattr__(self, "lon", float(lon))
    
    def _run(self) -> str:
        """Get comprehensive weather data using Open-Meteo (free API)"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": self.lat,
                "longitude": self.lon,
                "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,wind_direction_10m,weather_code",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
                "timezone": "auto",
                "forecast_days": 5
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            result = f"🌤️ Weather Forecast (Open-Meteo)\n"
            result += "="*60 + "\n\n"
            
            # Current conditions (first hour)
            hourly = data.get('hourly', {})
            times = hourly.get('time', [])
            if times:
                current_time = times[0]
                result += "📊 CURRENT CONDITIONS:\n"
                result += f"   Temperature: {hourly['temperature_2m'][0]:.1f}°C ({hourly['temperature_2m'][0] * 9/5 + 32:.1f}°F)\n"
                result += f"   Humidity: {hourly['relative_humidity_2m'][0]}%\n"
                result += f"   Wind: {hourly['wind_speed_10m'][0]:.1f} km/h ({hourly['wind_speed_10m'][0] * 0.621371:.1f} mph) from {hourly['wind_direction_10m'][0]:.0f}°\n"
                result += f"   Precipitation Chance: {hourly['precipitation_probability'][0]}%\n\n"
            
            # 5-day forecast
            daily = data.get('daily', {})
            daily_times = daily.get('time', [])
            if daily_times:
                result += "⏰ 5-DAY FORECAST:\n"
                for i in range(min(5, len(daily_times))):
                    date = daily_times[i]
                    result += f"   {date}: "
                    result += f"High {daily['temperature_2m_max'][i]:.0f}°C ({daily['temperature_2m_max'][i] * 9/5 + 32:.0f}°F), "
                    result += f"Low {daily['temperature_2m_min'][i]:.0f}°C ({daily['temperature_2m_min'][i] * 9/5 + 32:.0f}°F), "
                    result += f"Wind {daily['wind_speed_10m_max'][i]:.0f} km/h ({daily['wind_speed_10m_max'][i] * 0.621371:.0f} mph)\n"
                result += "\n"
            
            return result
            
        except Exception as e:
            return f"⚠️ Error connecting to Open-Meteo: {str(e)}"


class MarineTool(BaseTool):
    """Open-Meteo Marine API for detailed ocean conditions"""
    name: str = "Marine Conditions API"
    description: str = "Get detailed ocean conditions including wave height, swell period/direction, wind waves, ocean currents, and sea surface temperature from Open-Meteo"
    args_schema: Type[BaseModel] = MarineInput
    lat: float
    lon: float
    
    def __init__(self, lat: float, lon: float):
        super().__init__(lat=float(lat), lon=float(lon))
        object.__setattr__(self, "lat", float(lat))
        object.__setattr__(self, "lon", float(lon))
    
    def _run(self, date: str) -> str:
        """Get detailed ocean conditions"""
        try:
            url = "https://marine-api.open-meteo.com/v1/marine"
            params = {
                "latitude": self.lat,
                "longitude": self.lon,
                "hourly": "wave_height,wave_direction,wave_period,swell_wave_height,swell_wave_direction,swell_wave_period,wind_wave_height,wind_wave_direction,ocean_current_velocity,ocean_current_direction,sea_surface_temperature",
                "timezone": "auto",
                "start_date": date,
                "end_date": date
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            result = f"🌊 Marine Conditions (Open-Meteo)\n"
            result += "="*60 + "\n\n"
            
            hourly = data.get('hourly', {})
            times = hourly.get('time', [])
            
            # Show fishing hours (6 AM to 2 PM)
            result += "⏰ MARINE CONDITIONS (Fishing Hours 6AM-2PM):\n\n"
            for i in range(len(times)):
                time_str = times[i]
                hour = int(time_str.split('T')[1].split(':')[0])
                
                if 6 <= hour <= 14:
                    dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    result += f"📍 {dt.strftime('%I:%M %p')}:\n"
                    
                    # Wave conditions
                    wave_height_m = hourly['wave_height'][i]
                    wave_height_ft = wave_height_m * 3.28084
                    result += f"   Total Wave Height: {wave_height_m:.1f}m ({wave_height_ft:.1f}ft)\n"
                    result += f"   Wave Period: {hourly['wave_period'][i]:.0f} seconds\n"
                    result += f"   Wave Direction: {hourly['wave_direction'][i]:.0f}°\n"
                    
                    # Swell conditions
                    swell_height_m = hourly['swell_wave_height'][i]
                    swell_height_ft = swell_height_m * 3.28084
                    result += f"   Swell Height: {swell_height_m:.1f}m ({swell_height_ft:.1f}ft)\n"
                    result += f"   Swell Period: {hourly['swell_wave_period'][i]:.0f} seconds\n"
                    result += f"   Swell Direction: {hourly['swell_wave_direction'][i]:.0f}°\n"
                    
                    # Wind waves
                    wind_wave_m = hourly['wind_wave_height'][i]
                    wind_wave_ft = wind_wave_m * 3.28084
                    result += f"   Wind Wave Height: {wind_wave_m:.1f}m ({wind_wave_ft:.1f}ft)\n"
                    
                    # Ocean conditions
                    sea_temp_c = hourly['sea_surface_temperature'][i]
                    sea_temp_f = sea_temp_c * 9/5 + 32
                    result += f"   Sea Surface Temp: {sea_temp_c:.1f}°C ({sea_temp_f:.1f}°F)\n"
                    result += f"   Ocean Current: {hourly['ocean_current_velocity'][i]:.2f} m/s at {hourly['ocean_current_direction'][i]:.0f}°\n"
                    result += "\n"
            
            return result
            
        except Exception as e:
            return f"⚠️ Error fetching marine data from Open-Meteo: {str(e)}"


class BuoyTool(BaseTool):
    """NOAA Buoy real-time observations"""
    name: str = "NOAA Buoy Data"
    description: str = "Get real-time observations from the nearest NOAA buoy station including wind, waves, pressure, and water temperature"
    args_schema: Type[BaseModel] = BuoyInput
    buoy_station: str
    buoy_name: str
    
    def __init__(self, buoy_station: str, buoy_name: str):
        super().__init__(buoy_station=(buoy_station or ""), buoy_name=(buoy_name or "Unknown"))
        object.__setattr__(self, "buoy_station", (buoy_station or ""))
        object.__setattr__(self, "buoy_name", (buoy_name or "Unknown"))
    
    def _run(self, hours: int = 24) -> str:
        """Get real-time buoy observations"""
        if not self.buoy_station:
            return "⚠️ No NOAA buoy available for this location (may be too far from coast or no active buoys nearby)"
        
        try:
            url = f"https://www.ndbc.noaa.gov/data/realtime2/{self.buoy_station}.txt"
            df = pd.read_csv(url, sep='\s+', skiprows=[1], nrows=hours)
            
            result = f"🛟 NOAA Buoy {self.buoy_station} - {self.buoy_name}\n"
            result += "="*60 + "\n\n"
            
            latest = df.iloc[0]
            result += "📊 LATEST OBSERVATION:\n"
            result += f"   Time: {latest['#YY']}/{latest['MM']}/{latest['DD']} {latest['hh']}:{latest['mm']} UTC\n"
            
            if 'WDIR' in df.columns and latest['WDIR'] != 'MM':
                result += f"   Wind Direction: {latest['WDIR']}°\n"
            if 'WSPD' in df.columns and latest['WSPD'] != 'MM':
                result += f"   Wind Speed: {latest['WSPD']} m/s ({float(latest['WSPD']) * 2.237:.1f} mph)\n"
            if 'GST' in df.columns and latest['GST'] != 'MM':
                result += f"   Wind Gust: {latest['GST']} m/s ({float(latest['GST']) * 2.237:.1f} mph)\n"
            if 'WVHT' in df.columns and latest['WVHT'] != 'MM':
                result += f"   Wave Height: {latest['WVHT']} m ({float(latest['WVHT']) * 3.28:.1f} ft)\n"
            if 'DPD' in df.columns and latest['DPD'] != 'MM':
                result += f"   Dominant Wave Period: {latest['DPD']} sec\n"
            if 'APD' in df.columns and latest['APD'] != 'MM':
                result += f"   Average Wave Period: {latest['APD']} sec\n"
            if 'MWD' in df.columns and latest['MWD'] != 'MM':
                result += f"   Wave Direction: {latest['MWD']}°\n"
            if 'PRES' in df.columns and latest['PRES'] != 'MM':
                result += f"   Pressure: {latest['PRES']} hPa\n"
            if 'ATMP' in df.columns and latest['ATMP'] != 'MM':
                result += f"   Air Temperature: {latest['ATMP']}°C ({float(latest['ATMP']) * 9/5 + 32:.1f}°F)\n"
            if 'WTMP' in df.columns and latest['WTMP'] != 'MM':
                result += f"   Water Temperature: {latest['WTMP']}°C ({float(latest['WTMP']) * 9/5 + 32:.1f}°F)\n"
            
            return result
            
        except Exception as e:
            return f"⚠️ Error fetching buoy data: {str(e)}\n(Note: Some buoys may be offline or data unavailable)"


class TidesTool(BaseTool):
    """NOAA Tides & Currents API for tide predictions"""
    name: str = "NOAA Tide Predictions"
    description: str = "Get high and low tide predictions for the fishing date from the nearest NOAA tide station"
    args_schema: Type[BaseModel] = TidesInput
    tide_station: str
    tide_name: str
    
    def __init__(self, tide_station: str, tide_name: str):
        super().__init__(tide_station=(tide_station or ""), tide_name=(tide_name or "Unknown"))
        object.__setattr__(self, "tide_station", (tide_station or ""))
        object.__setattr__(self, "tide_name", (tide_name or "Unknown"))
    
    def _run(self, date: str) -> str:
        """Get tide predictions"""
        if not self.tide_station:
            return "⚠️ No tide station available for this location (may be inland or no tide stations nearby)"
        
        try:
            url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
            date_formatted = date.replace("-", "")
            params = {
                "begin_date": date_formatted,
                "end_date": date_formatted,
                "station": self.tide_station,
                "product": "predictions",
                "datum": "MLLW",
                "time_zone": "lst_ldt",
                "interval": "hilo",
                "units": "english",
                "application": "FishingConditionsApp",
                "format": "json"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            result = f"🌊 Tide Predictions for {date}\n"
            result += f"Station: {self.tide_station} - {self.tide_name}\n"
            result += "="*60 + "\n\n"
            
            predictions = data.get('predictions', [])
            if not predictions:
                return f"⚠️ No tide predictions available for {date}"
            
            result += "🌊 TIDE SCHEDULE:\n"
            for pred in predictions:
                tide_time = pred['t']
                tide_height = pred['v']
                tide_type = pred['type']
                
                if tide_type == 'H':
                    result += f"   🔵 HIGH Tide: {tide_time} - {tide_height} ft\n"
                else:
                    result += f"   🔴 LOW Tide:  {tide_time} - {tide_height} ft\n"
            
            result += "\n💡 FISHING TIP:\n"
            result += "   Best fishing typically occurs 1-2 hours before/after high tide,\n"
            result += "   or during slack tide periods when fish are actively feeding.\n"
            
            return result
            
        except Exception as e:
            return f"⚠️ Error fetching tide data: {str(e)}"


class NOAAWeatherTool(BaseTool):
    """NOAA Weather.gov API for official US weather forecasts"""
    name: str = "NOAA Weather Forecast"
    description: str = "Get official NOAA weather forecast for the fishing location (US only)"
    args_schema: Type[BaseModel] = NOAAWeatherInput
    lat: float
    lon: float
    
    def __init__(self, lat: float, lon: float):
        super().__init__(lat=float(lat), lon=float(lon))
        object.__setattr__(self, "lat", float(lat))
        object.__setattr__(self, "lon", float(lon))
    
    def _run(self) -> str:
        """Get official NOAA weather forecast"""
        try:
            url = f"https://api.weather.gov/points/{self.lat},{self.lon}"
            headers = {"User-Agent": "FishingConditionsApp/1.0"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 404:
                return "⚠️ NOAA Weather.gov forecast not available (location may be outside US)"
            
            response.raise_for_status()
            point_data = response.json()
            
            forecast_url = point_data['properties']['forecast']
            forecast_response = requests.get(forecast_url, headers=headers, timeout=10)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            result = f"🌤️ NOAA Official Weather Forecast\n"
            result += "="*60 + "\n\n"
            
            periods = forecast_data['properties']['periods'][:4]  # Next 2 days
            for period in periods:
                result += f"📅 {period['name']}:\n"
                result += f"   Temperature: {period['temperature']}°{period['temperatureUnit']}\n"
                result += f"   Wind: {period['windSpeed']} {period['windDirection']}\n"
                result += f"   Forecast: {period['shortForecast']}\n"
                result += f"   Details: {period['detailedForecast']}\n\n"
            
            return result
            
        except Exception as e:
            return f"⚠️ Error fetching NOAA weather: {str(e)}"


class MoonTool(BaseTool):
    """Get moon phase and position data"""
    name: str = "Moon Phase Data"
    description: str = "Get moon phase, moon rise/set times, and lunar data for fishing"
    args_schema: Type[BaseModel] = MoonInput
    lat: float
    lon: float
    
    def __init__(self, lat: float, lon: float):
        super().__init__(lat=float(lat), lon=float(lon))
        object.__setattr__(self, "lat", float(lat))
        object.__setattr__(self, "lon", float(lon))
    
    def _run(self, date: str) -> str:
        """Get moon phase and sun times"""
        try:
            url = "https://api.sunrise-sunset.org/json"
            params = {
                'lat': self.lat,
                'lng': self.lon,
                'date': date,
                'formatted': 0
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Calculate moon phase
            target_date = datetime.fromisoformat(date)
            days_since_new = (target_date.year - 2000) * 365.25 + target_date.timetuple().tm_yday
            moon_phase_days = days_since_new % 29.53
            phase_names = ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous", 
                          "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]
            phase_idx = int(moon_phase_days // 3.7) % 8
            
            result = f"🌙 Moon Data for {date}\n"
            result += "="*60 + "\n\n"
            result += f"Moon Phase: {phase_names[phase_idx]}\n"
            result += f"Days since new moon: {moon_phase_days:.1f}/29.5\n\n"
            result += "Sun Times:\n"
            result += f"  Sunrise: {data['results']['sunrise']}\n"
            result += f"  Sunset: {data['results']['sunset']}\n"
            result += f"  Solar Noon: {data['results']['solar_noon']}\n"
            result += f"  Day Length: {data['results']['day_length']}\n\n"
            
            if phase_idx in [0, 4]:  # New or Full moon
                result += "⚠️ Stronger tidal influence expected (new/full moon)\n"
            
            return result
            
        except Exception as e:
            return f"⚠️ Error fetching moon data: {str(e)}"


class OllamaWebSearchTool(BaseTool):
    """Web search for fishing reports and local information"""
    name: str = "Web Search"
    description: str = "Search the web for fishing reports, conditions, and local fishing information"
    args_schema: type[BaseModel] = WebSearchInput
    
    def _run(self, query: str) -> str:
        try:
            print(f"🔍 Searching for: {query}")
            results = ollama.web_search(query)
            
            if not results or not results.get('results'):
                print("⚠️ No search results found")
                return "No search results found. Try a different search query."
            
            formatted = []
            for i, r in enumerate(results['results'][:5], 1):
                formatted.append(
                    f"{i}. {r['title']}\n{r['url']}\n{r['content'][:200]}..."
                )
            
            result = "\n\n".join(formatted)
            print(f"✅ Found {len(results.get('results', []))} results")
            return result
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            return f"Search error: {str(e)}"


class ScrapeURLTool(BaseTool):
    """Scrape text content from a specific URL using ScrapeWebsiteTool"""
    name: str = "Scrape URL"
    description: str = "Fetch and return the main text content from a given URL"
    args_schema: type[BaseModel] = ScrapeURLInput

    def _run(self, url: str) -> str:
        try:
            tool = ScrapeWebsiteTool(website_url=url)
            return tool.run()
        except Exception as e:
            return f"Scrape error: {str(e)}"


def get_tools(config: dict):
    """Factory function to create tool instances following CrewAI patterns"""
    tools = []
    
    # Weather tool (always available - uses free Open-Meteo API)
    tools.append(WeatherTool(config['FISHING_LAT'], config['FISHING_LON']))
    
    # Marine conditions tool (always available)
    tools.append(MarineTool(config['FISHING_LAT'], config['FISHING_LON']))
    
    # Buoy tool (if station available)
    if config.get('BUOY_STATION'):
        tools.append(BuoyTool(config.get('BUOY_STATION', ''), config.get('BUOY_NAME', 'Unknown')))
    
    # Tides tool (if station available)
    if config.get('TIDE_STATION'):
        tools.append(TidesTool(config.get('TIDE_STATION', ''), config.get('TIDE_STATION_NAME', 'Unknown')))
    
    # NOAA Weather tool (always try)
    tools.append(NOAAWeatherTool(config['FISHING_LAT'], config['FISHING_LON']))
    
    # Moon tool (always available)
    tools.append(MoonTool(config['FISHING_LAT'], config['FISHING_LON']))
    
    return tools


def get_search_tools():
    """Get web search tools for fishing research"""
    return [
        OllamaWebSearchTool(),
        ScrapeURLTool(),
    ]
