"""
Dynamic Location Discovery Module for Fishing Conditions
Works ANYWHERE - no hardcoded values!
Automatically finds nearest NOAA buoy stations and tide stations for any location
"""

import requests
import math
from typing import Dict, Tuple, Optional, List
import xml.etree.ElementTree as ET


class FishingLocationDiscovery:
    """Discover and configure fishing location parameters automatically for ANY location"""
    
    def __init__(self, location_name: str = None, lat: float = None, lon: float = None):
        """
        Initialize with either a location name OR coordinates
        
        Args:
            location_name: e.g. "Half Moon Bay, CA" or "Boston Harbor, MA"
            lat: Latitude (if you have coordinates)
            lon: Longitude (if you have coordinates)
        """
        self.location_name = location_name
        self.lat = lat
        self.lon = lon
        
        # If only name provided, geocode it
        if location_name and (lat is None or lon is None):
            self.lat, self.lon = self.geocode_location(location_name)
            print(f"📍 Geocoded '{location_name}' to: {self.lat:.4f}, {self.lon:.4f}")
        
        # Storage for discovered stations
        self.nearest_buoy = None
        self.nearest_tide_station = None
        
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the distance between two points on Earth in kilometers
        """
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def geocode_location(self, location_name: str) -> Tuple[float, float]:
        """
        Geocode a location name to coordinates using Open-Meteo's free geocoding API
        
        Args:
            location_name: Location name like "Half Moon Bay, CA" or "Boston, MA"
            
        Returns:
            Tuple of (latitude, longitude)
        """
        try:
            # Use Open-Meteo's free geocoding API (no key required!)
            url = "https://geocoding-api.open-meteo.com/v1/search"
            
            # Clean the location name for better results
            cleaned_name = location_name.split(',')[0].strip()
            
            params = {
                "name": cleaned_name,
                "count": 5,
                "language": "en",
                "format": "json"
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('results'):
                # Show all results so user can pick if needed
                print(f"\n   📍 Found {len(data['results'])} location(s):")
                for i, result in enumerate(data['results'][:5]):
                    country = result.get('country', '')
                    state = result.get('admin1', '')
                    name = result.get('name', '')
                    print(f"      {i+1}. {name}, {state}, {country} ({result['latitude']:.4f}, {result['longitude']:.4f})")
                
                # Use the first result
                result = data['results'][0]
                lat = result['latitude']
                lon = result['longitude']
                
                return lat, lon
            else:
                raise ValueError(f"Could not geocode location: {location_name}")
                
        except Exception as e:
            raise ValueError(f"Geocoding failed: {str(e)}")
    
    def find_nearest_buoy(self, max_distance_km: float = 200) -> Optional[Dict]:
        """
        Find the nearest NOAA buoy station by querying the NDBC active stations
        Works for ANY location in the world where NOAA has buoys
        
        Args:
            max_distance_km: Maximum search radius in kilometers (default 200km)
            
        Returns:
            Dict with buoy information or None if no buoy found
        """
        print(f"\n🔍 Searching for NOAA buoys within {max_distance_km} km...")
        
        try:
            # Get ALL active NDBC stations from NOAA
            url = "https://www.ndbc.noaa.gov/activestations.xml"
            
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            nearest_station = None
            min_distance = float('inf')
            stations_checked = 0
            
            # Check ALL stations dynamically
            for station in root.findall('.//station'):
                try:
                    station_id = station.get('id')
                    station_lat = float(station.get('lat'))
                    station_lon = float(station.get('lon'))
                    station_name = station.get('name', 'Unknown')
                    station_type = station.get('type', '')
                    
                    # Only consider actual buoys (not fixed platforms like tide gauges)
                    if station_type not in ('buoy', 'other', 'usv'):
                        continue
                    
                    # Prefer stations with met data, but also accept stations that might have wave data
                    # (some NDBC stations have wave data but met='n')
                    
                    stations_checked += 1
                    
                    # Calculate distance
                    distance = self.haversine_distance(
                        self.lat, self.lon,
                        station_lat, station_lon
                    )
                    
                    if distance < min_distance and distance <= max_distance_km:
                        min_distance = distance
                        nearest_station = {
                            'id': station_id,
                            'name': station_name,
                            'latitude': station_lat,
                            'longitude': station_lon,
                            'distance_km': round(distance, 2),
                            'distance_nm': round(distance * 0.539957, 2),
                            'data_url': f"https://www.ndbc.noaa.gov/data/realtime2/{station_id}.txt"
                        }
                        
                except (ValueError, TypeError, AttributeError):
                    continue
            
            print(f"   ✓ Checked {stations_checked} active NOAA buoy stations")
            
            if nearest_station:
                self.nearest_buoy = nearest_station
                print(f"   ✓ Nearest Buoy: Station {nearest_station['id']} - {nearest_station['name']}")
                print(f"   ✓ Distance: {nearest_station['distance_km']} km ({nearest_station['distance_nm']} nm)")
                print(f"   ✓ Location: {nearest_station['latitude']:.3f}°, {nearest_station['longitude']:.3f}°")
                return nearest_station
            else:
                print(f"   ⚠️  No NOAA buoy found within {max_distance_km} km of this location")
                print(f"   💡 Try increasing max_distance_km or check if NOAA has coverage in this area")
                return None
                
        except Exception as e:
            print(f"   ❌ Error querying NOAA buoy database: {str(e)}")
            return None
    
    def find_nearest_tide_station(self, max_distance_km: float = 100) -> Optional[Dict]:
        """
        Find the nearest NOAA tide station by querying the CO-OPS metadata API
        Works for ANY coastal location in the US
        
        Args:
            max_distance_km: Maximum search radius in kilometers (default 100km)
            
        Returns:
            Dict with tide station information or None if no station found
        """
        print(f"\n🔍 Searching for NOAA tide stations within {max_distance_km} km...")
        
        try:
            # Get ALL NOAA CO-OPS stations
            url = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json"
            
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            nearest_station = None
            min_distance = float('inf')
            stations_checked = 0
            
            # Check ALL tide stations dynamically
            for station in data.get('stations', []):
                try:
                    station_id = station.get('id')
                    station_lat = float(station.get('lat'))
                    station_lon = float(station.get('lng'))
                    station_name = station.get('name', 'Unknown')
                    
                    # Only consider stations with tide prediction capability
                    # products is a dict, so check if 'self' URL exists
                    products = station.get('products', {})
                    if not isinstance(products, dict) or 'self' not in products:
                        continue
                    
                    stations_checked += 1
                    
                    # Calculate distance
                    distance = self.haversine_distance(
                        self.lat, self.lon,
                        station_lat, station_lon
                    )
                    
                    if distance < min_distance and distance <= max_distance_km:
                        min_distance = distance
                        nearest_station = {
                            'id': station_id,
                            'name': station_name,
                            'latitude': station_lat,
                            'longitude': station_lon,
                            'distance_km': round(distance, 2),
                            'distance_nm': round(distance * 0.539957, 2),
                            'state': station.get('state', 'N/A')
                        }
                        
                except (ValueError, TypeError, KeyError):
                    continue
            
            print(f"   ✓ Checked {stations_checked} NOAA tide prediction stations")
            
            if nearest_station:
                self.nearest_tide_station = nearest_station
                print(f"   ✓ Nearest Tide Station: {nearest_station['id']} - {nearest_station['name']}")
                print(f"   ✓ Distance: {nearest_station['distance_km']} km ({nearest_station['distance_nm']} nm)")
                print(f"   ✓ Location: {nearest_station['latitude']:.3f}°, {nearest_station['longitude']:.3f}°")
                return nearest_station
            else:
                print(f"   ⚠️  No tide station found within {max_distance_km} km")
                print(f"   💡 Try increasing max_distance_km")
                return None
                
        except Exception as e:
            print(f"   ❌ Error querying NOAA tide station database: {str(e)}")
            return None
    
    def discover_all(self, buoy_radius_km: float = 200, tide_radius_km: float = 100) -> Dict:
        """
        Discover all location parameters automatically
        
        Args:
            buoy_radius_km: Search radius for buoys
            tide_radius_km: Search radius for tide stations
            
        Returns:
            Dict with all discovered parameters
        """
        print("="*70)
        print("🎣 FISHING LOCATION DISCOVERY")
        print("="*70)
        
        # Find nearest stations
        buoy = self.find_nearest_buoy(max_distance_km=buoy_radius_km)
        tide = self.find_nearest_tide_station(max_distance_km=tide_radius_km)
        
        result = {
            'location_name': self.location_name,
            'latitude': self.lat,
            'longitude': self.lon,
            'nearest_buoy': buoy,
            'nearest_tide_station': tide
        }
        
        print("\n" + "="*70)
        print("✅ DISCOVERY COMPLETE")
        print("="*70)
        
        return result
    
    def get_config_dict(self) -> Dict:
        """
        Get a configuration dictionary for use in your CrewAI agents
        
        Returns:
            Dict ready to be used as configuration
        """
        config = {
            'FISHING_LOCATION': self.location_name or f"{self.lat:.4f}, {self.lon:.4f}",
            'FISHING_LAT': self.lat,
            'FISHING_LON': self.lon,
        }
        
        if self.nearest_buoy:
            config.update({
                'BUOY_STATION': self.nearest_buoy['id'],
                'BUOY_NAME': self.nearest_buoy['name'],
                'BUOY_LAT': self.nearest_buoy['latitude'],
                'BUOY_LON': self.nearest_buoy['longitude'],
                'BUOY_DISTANCE_KM': self.nearest_buoy['distance_km']
            })
        else:
            config.update({
                'BUOY_STATION': None,
                'BUOY_NAME': 'No buoy available',
                'BUOY_LAT': None,
                'BUOY_LON': None,
                'BUOY_DISTANCE_KM': None
            })
        
        if self.nearest_tide_station:
            config.update({
                'TIDE_STATION': self.nearest_tide_station['id'],
                'TIDE_STATION_NAME': self.nearest_tide_station['name'],
                'TIDE_STATION_LAT': self.nearest_tide_station['latitude'],
                'TIDE_STATION_LON': self.nearest_tide_station['longitude'],
                'TIDE_DISTANCE_KM': self.nearest_tide_station['distance_km']
            })
        else:
            config.update({
                'TIDE_STATION': None,
                'TIDE_STATION_NAME': 'No tide station available',
                'TIDE_STATION_LAT': None,
                'TIDE_STATION_LON': None,
                'TIDE_DISTANCE_KM': None
            })
        
        return config
