#!/usr/bin/env python3
"""
Weather Data Map Visualization
Interactive map with popup information for weather stations
"""

import json
import folium
from folium import plugins
import pandas as pd
import os
from datetime import datetime

class WeatherMapVisualizer:
    def __init__(self, data_file=None):
        """
        Initialize the weather map visualizer

        Args:
            data_file (str): Path to weather data JSON file
        """
        self.data_file = data_file or "output/weather_data_20260224_161848.json"
        self.weather_data = []
        self.load_data()

    def load_data(self):
        """Load weather data from JSON file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.weather_data = json.load(f)
            print(f"Loaded {len(self.weather_data)} weather stations")
        except FileNotFoundError:
            print(f"Error: Could not find data file {self.data_file}")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")

    def get_color_for_temperature(self, temp):
        """
        Get color based on temperature

        Args:
            temp (str): Temperature value

        Returns:
            str: Color code
        """
        try:
            temp_val = float(temp)
            if temp_val < 10:
                return 'blue'
            elif temp_val < 15:
                return 'lightblue'
            elif temp_val < 20:
                return 'green'
            elif temp_val < 25:
                return 'orange'
            elif temp_val < 30:
                return 'red'
            else:
                return 'darkred'
        except (ValueError, TypeError):
            return 'gray'

    def create_popup_html(self, station):
        """
        Create HTML content for popup window

        Args:
            station (dict): Station data

        Returns:
            str: HTML content
        """
        elements = station.get('weather_elements', {})

        html = f"""
        <div style="font-family: Arial, sans-serif; width: 250px;">
            <h3 style="margin: 0; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">
                {station.get('station_name', 'Unknown')}
            </h3>
            <p style="margin: 5px 0; color: #7f8c8d;">
                <strong>站點ID:</strong> {station.get('station_id', 'N/A')}<br>
                <strong>位置:</strong> {station.get('location', 'N/A')}<br>
                <strong>觀測時間:</strong> {station.get('observation_time', 'N/A')}
            </p>

            <h4 style="margin: 10px 0 5px 0; color: #34495e;">氣象資訊</h4>
            <table style="width: 100%; border-collapse: collapse;">
        """

        # Add weather elements to table
        element_display = {
            'TEMP': ('溫度', '°C'),
            'HUMD': ('濕度', '%'),
            'PRES': ('氣壓', 'hPa'),
            'WDSD': ('風速', 'm/s'),
            'WDIR': ('風向', '°'),
            'RAIN': ('降水量', 'mm'),
            'UVI': ('UV指數', ''),
            'SUN': ('日照時數', '小時')
        }

        for element, (name, unit) in element_display.items():
            if element in elements:
                value = elements[element]['value']
                display_unit = elements[element]['unit'] if elements[element]['unit'] else unit
                html += f"""
                <tr style="border-bottom: 1px solid #ecf0f1;">
                    <td style="padding: 3px; font-weight: bold;">{name}:</td>
                    <td style="padding: 3px; text-align: right;">{value} {display_unit}</td>
                </tr>
                """

        html += f"""
            </table>

            <p style="margin: 10px 0 5px 0;">
                <strong>天氣狀況:</strong> {station.get('raw_weather', 'N/A')}<br>
                <strong>能見度:</strong> {station.get('visibility', 'N/A')}
            </p>

            <p style="margin: 5px 0; font-size: 12px; color: #95a5a6;">
                座標: {station.get('coordinates', {}).get('lat', 'N/A')},
                {station.get('coordinates', {}).get('lon', 'N/A')}
            </p>
        </div>
        """

        return html

    def create_map(self):
        """
        Create interactive weather map

        Returns:
            folium.Map: Interactive map object
        """
        if not self.weather_data:
            print("No weather data available")
            return None

        # Create map centered on Taiwan
        taiwan_center = [23.8, 120.9]
        m = folium.Map(
            location=taiwan_center,
            zoom_start=7,
            tiles='OpenStreetMap'
        )

        # Add tile layers
        folium.TileLayer('OpenStreetMap').add_to(m)
        folium.TileLayer(
            tiles='CartoDB positron',
            attr='© CartoDB'
        ).add_to(m)
        folium.TileLayer(
            tiles='Stamen Terrain',
            attr='Map tiles by Stamen Design, under CC BY 3.0'
        ).add_to(m)

        # Create feature groups for different data types
        temp_group = folium.FeatureGroup(name="溫度分布")
        weather_group = folium.FeatureGroup(name="天氣狀況")

        # Add markers for each weather station
        for station in self.weather_data:
            coords = station.get('coordinates', {})
            lat = coords.get('lat')
            lon = coords.get('lon')

            if lat == 'N/A' or lon == 'N/A' or lat is None or lon is None:
                continue

            try:
                lat = float(lat)
                lon = float(lon)
            except (ValueError, TypeError):
                continue

            # Get temperature for color coding
            temp = station.get('weather_elements', {}).get('TEMP', {}).get('value', '20')
            color = self.get_color_for_temperature(temp)

            # Create popup HTML
            popup_html = self.create_popup_html(station)

            # Create marker with custom icon
            icon = folium.Icon(
                color=color,
                icon='cloud',
                prefix='fa'
            )

            # Add marker to temperature group
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{station.get('station_name', 'Unknown')} - {temp}°C",
                icon=icon
            ).add_to(temp_group)

            # Add weather text marker
            weather_text = station.get('raw_weather', 'N/A')
            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=folium.Popup(f"<strong>天氣:</strong> {weather_text}", max_width=200),
                tooltip=weather_text,
                color='purple',
                fill=True,
                fillColor='purple',
                fillOpacity=0.6
            ).add_to(weather_group)

        # Add feature groups to map
        temp_group.add_to(m)
        weather_group.add_to(m)

        # Add layer control
        folium.LayerControl().add_to(m)

        # Add legend
        legend_html = '''
        <div style="position: fixed;
                    bottom: 50px; left: 50px; width: 150px; height: 200px;
                    background-color: white; border:2px solid grey; z-index:9999;
                    font-size:14px; padding: 10px">
        <h4 style="margin: 0 0 10px 0;">溫度圖例</h4>
        <p><i class="fa fa-circle" style="color:blue"></i> < 10°C</p>
        <p><i class="fa fa-circle" style="color:lightblue"></i> 10-15°C</p>
        <p><i class="fa fa-circle" style="color:green"></i> 15-20°C</p>
        <p><i class="fa fa-circle" style="color:orange"></i> 20-25°C</p>
        <p><i class="fa fa-circle" style="color:red"></i> 25-30°C</p>
        <p><i class="fa fa-circle" style="color:darkred"></i> > 30°C</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

        return m

    def save_map(self, output_file=None):
        """
        Save map to HTML file

        Args:
            output_file (str): Output filename
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"output/weather_map_{timestamp}.html"

        map_obj = self.create_map()
        if map_obj:
            map_obj.save(output_file)
            print(f"Weather map saved to: {output_file}")
            return output_file
        return None

    def show_statistics(self):
        """Display basic statistics of the weather data"""
        if not self.weather_data:
            print("No data available for statistics")
            return

        print(f"\n=== 氣象資料統計 ===")
        print(f"總測站數量: {len(self.weather_data)}")

        # Temperature statistics
        temps = []
        for station in self.weather_data:
            temp = station.get('weather_elements', {}).get('TEMP', {}).get('value')
            if temp and temp != 'N/A':
                try:
                    temps.append(float(temp))
                except ValueError:
                    pass

        if temps:
            print(f"溫度範圍: {min(temps):.1f}°C - {max(temps):.1f}°C")
            print(f"平均溫度: {sum(temps)/len(temps):.1f}°C")

        # Weather conditions
        weather_conditions = {}
        for station in self.weather_data:
            weather = station.get('raw_weather', 'N/A')
            weather_conditions[weather] = weather_conditions.get(weather, 0) + 1

        print(f"\n天氣狀況分布:")
        for weather, count in sorted(weather_conditions.items()):
            print(f"  {weather}: {count} 個測站")

def main():
    """Main function to create and display weather map"""
    try:
        # Initialize visualizer
        visualizer = WeatherMapVisualizer()

        # Show statistics
        visualizer.show_statistics()

        # Create and save map
        print("\nCreating weather map...")
        map_file = visualizer.save_map()

        if map_file:
            print(f"\n✅ 天氣地圖已成功建立！")
            print(f"📁 檔案位置: {map_file}")
            print(f"🌐 請用瀏覽器開啟檔案查看互動式地圖")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
