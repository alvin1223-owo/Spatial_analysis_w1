#!/usr/bin/env python3
"""
CWA Weather API Integration
API: O-A0003-001 (10-minute comprehensive weather data)
"""

import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CWAWeatherAPI:
    def __init__(self):
        self.api_key = os.getenv('CWA_API_KEY')
        self.base_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
        self.dataset_id = "O-A0003-001"

        if not self.api_key:
            raise ValueError("CWA_API_KEY not found in environment variables")

    def get_weather_data(self, location_name=None, limit=100):
        """
        Get 10-minute comprehensive weather data

        Args:
            location_name (str): Specific location name (optional)
            limit (int): Number of records to retrieve (default: 100)

        Returns:
            dict: Weather data from CWA API
        """
        url = f"{self.base_url}/{self.dataset_id}"

        params = {
            'Authorization': self.api_key,
            'format': 'JSON',
            'limit': limit
        }

        if location_name:
            params['locationName'] = location_name

        try:
            response = requests.get(url, params=params, timeout=30, verify=False)
            response.raise_for_status()

            data = response.json()

            if data.get('success') == 'true':
                return data
            else:
                error_msg = data.get('message', 'Unknown error')
                raise Exception(f"API Error: {error_msg}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON decode error: {str(e)}")

    def parse_weather_data(self, data):
        """
        Parse and format weather data

        Args:
            data (dict): Raw API response data

        Returns:
            list: Parsed weather information
        """
        if not data.get('success') == 'true':
            return []

        records = data.get('records', {})
        stations = records.get('Station', [])

        parsed_data = []

        for station in stations:
            station_name = station.get('StationName', 'Unknown')
            station_id = station.get('StationId', 'N/A')

            # Get observation time
            obs_time = station.get('ObsTime', {}).get('DateTime', 'N/A')

            # Get location info
            geo_info = station.get('GeoInfo', {})
            county = geo_info.get('CountyName', 'N/A')
            town = geo_info.get('TownName', 'N/A')

            # Get coordinates (prefer WGS84)
            coordinates = {'lat': 'N/A', 'lon': 'N/A'}
            coords_list = geo_info.get('Coordinates', [])
            for coord in coords_list:
                if coord.get('CoordinateName') == 'WGS84':
                    coordinates = {
                        'lat': coord.get('StationLatitude', 'N/A'),
                        'lon': coord.get('StationLongitude', 'N/A')
                    }
                    break
                elif coordinates['lat'] == 'N/A':  # fallback to first available
                    coordinates = {
                        'lat': coord.get('StationLatitude', 'N/A'),
                        'lon': coord.get('StationLongitude', 'N/A')
                    }

            # Parse weather elements
            weather_elements = {}
            weather_element = station.get('WeatherElement', {})

            # Map common weather data
            element_mapping = {
                'AirTemperature': {'name': 'TEMP', 'unit': '°C'},
                'RelativeHumidity': {'name': 'HUMD', 'unit': '%'},
                'AirPressure': {'name': 'PRES', 'unit': 'hPa'},
                'WindSpeed': {'name': 'WDSD', 'unit': 'm/s'},
                'WindDirection': {'name': 'WDIR', 'unit': 'degrees'},
                'Precipitation': {'name': 'RAIN', 'unit': 'mm'},
                'UVIndex': {'name': 'UVI', 'unit': 'index'},
                'SunshineDuration': {'name': 'SUN', 'unit': 'hours'},
                'Weather': {'name': 'WEATHER', 'unit': ''}
            }

            for api_field, mapping in element_mapping.items():
                if api_field in weather_element:
                    value = weather_element[api_field]
                    # Handle nested precipitation
                    if api_field == 'Precipitation' and isinstance(value, dict):
                        value = value.get('Precipitation', '0.0')

                    weather_elements[mapping['name']] = {
                        'value': str(value),
                        'unit': mapping['unit']
                    }

            parsed_data.append({
                'station_name': station_name,
                'station_id': station_id,
                'location': f"{county}{town}",
                'coordinates': coordinates,
                'observation_time': obs_time,
                'weather_elements': weather_elements,
                'raw_weather': weather_element.get('Weather', ''),
                'visibility': weather_element.get('VisibilityDescription', 'N/A')
            })

        return parsed_data

    def save_to_json(self, data, filename=None):
        """
        Save weather data to JSON file

        Args:
            data: Weather data to save
            filename (str): Output filename (optional)
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"weather_data_{timestamp}.json"

        output_path = os.path.join("output", filename)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"Data saved to: {output_path}")
            return output_path

        except Exception as e:
            print(f"Error saving data: {str(e)}")
            return None

def main():
    """Main function to demonstrate API usage"""
    try:
        # Initialize API client
        api = CWAWeatherAPI()

        print("Fetching weather data from CWA API...")

        # Get weather data
        raw_data = api.get_weather_data()

        # Save raw response for debugging
        raw_output_file = api.save_to_json(raw_data, f"raw_api_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        # Parse the data
        parsed_data = api.parse_weather_data(raw_data)

        # Display summary
        print(f"\nRetrieved data for {len(parsed_data)} locations")

        # Debug: Show raw data structure
        if raw_data.get('success') == 'true':
            records = raw_data.get('records', {})
            print(f"Raw data structure keys: {list(records.keys())}")
            if 'Station' in records:
                print(f"Number of stations in raw data: {len(records['Station'])}")
                # Show first station structure
                if records['Station']:
                    print(f"First station keys: {list(records['Station'][0].keys())}")
        else:
            print(f"API response not successful: {raw_data}")

        # Show first location as example
        if parsed_data:
            first_station = parsed_data[0]
            print(f"\nExample - {first_station['station_name']} ({first_station['location']}):")
            print(f"  Station ID: {first_station['station_id']}")
            print(f"  Observation Time: {first_station['observation_time']}")
            print(f"  Coordinates: {first_station['coordinates']}")
            print(f"  Weather: {first_station['raw_weather']}")
            print(f"  Visibility: {first_station['visibility']}")

            # Show key weather elements
            elements = first_station['weather_elements']
            key_elements = ['TEMP', 'HUMD', 'PRES', 'WDSD', 'WDIR', 'RAIN']

            print("  Weather Elements:")
            for element in key_elements:
                if element in elements:
                    elem_data = elements[element]
                    print(f"    {element}: {elem_data['value']} {elem_data['unit']}")
        else:
            print("No parsed data available. Check raw response file for details.")

        # Save to file
        output_file = api.save_to_json(parsed_data)

        print(f"\nWeather data successfully retrieved and saved!")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
