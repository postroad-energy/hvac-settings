"""
Weather forecast module for HVAC settings.
"""
import json
import urllib3
from urllib3 import Retry
import time
import haversine
from haversine import Unit
from datetime import datetime, timedelta
import pytz
import pandas as pd

# Constants
OPEN_STREET_MAP = "https://nominatim.openstreetmap.org/search.php?country=US&postalcode="
LAT_LON_FORMAT = "&format=jsonv2"
NWC_POINTS_BASE_URL = "https://api.weather.gov/points/"
STATION_BASE_URL = "https://api.weather.gov/stations/"
STATION_LATEST = "/observations/latest"
FORECAST_BASE_URL = "https://api.weather.gov/gridpoints/"
HOURLY_FORECAST = "/forecast/hourly"
SUCCESS = 200
FAHRENHEIT = 9/5
THIRTY_TWO = 32
TWO_DEC_PLACES = "%.2f"
FOUR_DEC_PLACES = "%.4f"
MILES_PER_HOUR = 1.609
RADIUS_LIMIT = 15.00
ERROR_STATUS_CODE = 400

class WeatherForecast:
    """
    Class for retrieving weather forecast data based on location coordinates or US zip code.
    """
    def __init__(self, latitude: float = None, longitude: float = None, zip_code: str = None):
        """
        Initialize WeatherForecast with location coordinates or zip code.
        
        Args:
            latitude (float, optional): Location latitude
            longitude (float, optional): Location longitude
            zip_code (str, optional): US zip code
            
        Raises:
            ValueError: If neither zip_code nor both latitude and longitude are provided
        """
        if zip_code:
            self._get_coordinates_from_zip(zip_code)
        elif latitude is not None and longitude is not None:
            self.latitude = latitude
            self.longitude = longitude
        else:
            raise ValueError("Either zip_code or both latitude and longitude must be provided")
        self.grid_id = None
        self.grid_x = None
        self.grid_y = None
    
    def _get_coordinates_from_zip(self, zip_code: str) -> None:
        """Get coordinates from zip code using OpenStreetMap."""
        zip_code_url = OPEN_STREET_MAP + zip_code + LAT_LON_FORMAT
        coordinates_results = self._get_requests(zip_code_url)
        
        if coordinates_results is None or not coordinates_results:
            raise ValueError(f"Could not get coordinates for zip code {zip_code}")
        
        self.latitude = float(FOUR_DEC_PLACES % float(coordinates_results[0]["lat"]))
        self.longitude = float(FOUR_DEC_PLACES % float(coordinates_results[0]["lon"]))
    
    def _get_requests(self, url: str) -> dict:
        """Make HTTP GET request with retries."""
        data = None
        retries = Retry(connect=3, status=2)
        headers = {'User-Agent': 'sampleWeatherAPI.com'}
        try:
            http = urllib3.PoolManager()
            response = http.request("GET", url, headers=headers, retries=retries)
            # print(f"Response status: {response.status}")
            if response.status == SUCCESS:
                data = json.loads(response.data)
                # print(f"Response data: {json.dumps(data, indent=2)}")
            else:
                error_info = json.loads(response.data)
                status_code = error_info.get("status", ERROR_STATUS_CODE)
                detail = error_info.get("detail", "Unknown error")
                self._log_error(status_code, str(detail))
        except urllib3.exceptions.HTTPError as e:
            self._log_error(ERROR_STATUS_CODE, str(e))
        except Exception as e:
            self._log_error(ERROR_STATUS_CODE, str(e))
        return data
    
    def _log_error(self, status: int, error_message: str) -> None:
        """Log error messages."""
        print(f"\nERROR - Status {status}: {error_message}")
    
    def _get_grid_coordinates(self) -> None:
        """Get grid coordinates for the location."""
        if self.grid_id is not None:
            return
            
        coordinates = f"{self.latitude},{self.longitude}"
        nwc_points_full_url = NWC_POINTS_BASE_URL + coordinates
        metadata = self._get_requests(nwc_points_full_url)
        if metadata is None:
            raise ValueError("Could not get weather metadata")
            
        properties = metadata["properties"]
        self.grid_id = properties["gridId"]
        self.grid_x = properties["gridX"]
        self.grid_y = properties["gridY"]
    
    def get_forecast(self, hours: int = 24) -> dict:
        """
        Get hourly temperature forecasts for the specified number of hours.
        
        Args:
            hours (int): Number of hours to forecast (default: 24)
            
        Returns:
            dict: Hourly temperature forecasts
            
        Raises:
            ValueError: If weather data cannot be retrieved or hours is invalid
        """
        if hours < 1 or hours > 156:  # NWS provides up to 156 hours of hourly forecast
            raise ValueError("Hours must be between 1 and 156")
            
        self._get_grid_coordinates()
        
        forecast_url = f"{FORECAST_BASE_URL}{self.grid_id}/{self.grid_x},{self.grid_y}{HOURLY_FORECAST}"
        forecast_data = self._get_requests(forecast_url)
        
        if forecast_data is None:
            raise ValueError("Could not get forecast data")
            
        periods = forecast_data["properties"]["periods"]
        current_time = datetime.now(pytz.UTC)
        hourly_forecasts = []
        
        for period in periods:
            period_time = datetime.fromisoformat(period["startTime"].replace("Z", "+00:00"))
            hours_ahead = int((period_time - current_time).total_seconds() / 3600)
            
            if hours_ahead >= 0 and hours_ahead < hours:
                hourly_forecasts.append({
                    "hour": hours_ahead + 1,  # Make hours 1-based instead of 0-based
                    "time": period["startTime"],
                    "temperature": period["temperature"],
                    "humidity": period["relativeHumidity"]["value"],
                    "is_daytime": period.get("isDaytime", True)
                })
        
        if not hourly_forecasts:
            raise ValueError(f"Could not find forecasts for the next {hours} hours")
            
        return {
            "hourly_forecasts": hourly_forecasts,
            "generated_at": current_time.isoformat(),
            "hours_forecast": hours,
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "grid_id": self.grid_id
            }
        }
    
    def get_current_weather(self) -> dict:
        """
        Get current weather observation for the specified location.
        
        Returns:
            dict: Current weather data
            
        Raises:
            ValueError: If weather data cannot be retrieved
        """
        coordinates = f"{self.latitude},{self.longitude}"
        nwc_points_full_url = NWC_POINTS_BASE_URL + coordinates
        metadata = self._get_requests(nwc_points_full_url)
        if metadata is None:
            raise ValueError("Could not get weather metadata")
            
        observation_url = metadata["properties"]["observationStations"]
        observation_stations = self._get_requests(observation_url)
        if observation_stations is None:
            raise ValueError("Could not get observation stations")
            
        list_of_station_id = observation_stations["features"]
        current_weather_data = None
        
        for station in list_of_station_id:
            station_id = station["properties"]["stationIdentifier"]
            current_weather_data = self._validate_and_format_weather_data(station_id, coordinates)
            
            if current_weather_data is not None:
                obs_coordinates = station["geometry"]["coordinates"]
                nearby_zip_code_coordinates = (obs_coordinates[1], abs(obs_coordinates[0]))
                zip_code_coordinates = (self.latitude, abs(self.longitude))
                actual_distance = haversine.haversine(
                    nearby_zip_code_coordinates,
                    zip_code_coordinates,
                    unit=Unit.KILOMETERS
                )
                
                if actual_distance <= RADIUS_LIMIT:
                    break
                current_weather_data = None
        
        if current_weather_data is None:
            raise ValueError("Could not get valid weather data")
            
        return current_weather_data
    
    def _validate_and_format_weather_data(self, station_id: str, zip_code: str) -> dict:
        """Validate and format weather data from a station."""
        observation_station_full_url = STATION_BASE_URL + station_id + STATION_LATEST
        latest_observation_data = self._get_requests(observation_station_full_url)
        if latest_observation_data is None:
            return None
            
        properties = latest_observation_data["properties"]
        
        required_fields = {
            "temperature": "Temperature",
            "windDirection": "Wind Direction",
            "windSpeed": "Wind Speed",
            "relativeHumidity": "Relative Humidity"
        }
        
        for field, name in required_fields.items():
            if properties[field]["value"] is None:
                self._log_error(ERROR_STATUS_CODE, f"{name} is null for {zip_code}")
                return None
        
        temperature = (properties["temperature"]["value"] * FAHRENHEIT) + THIRTY_TWO
        temperature = float(TWO_DEC_PLACES % temperature)
        wind_speed = float(TWO_DEC_PLACES % (properties["windSpeed"]["value"] / MILES_PER_HOUR))
        relative_humidity = float(TWO_DEC_PLACES % properties["relativeHumidity"]["value"])
        wind_direction = properties["windDirection"]["value"]
        
        formatted_data = {
            "resource_id": int(time.time() * 1000),
            "temperature": temperature,
            "humidity": relative_humidity,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction
        }
        return formatted_data


if __name__ == "__main__":
    weather = WeatherForecast(zip_code="94305")
    print("\nCurrent Weather:")
    print(weather.get_current_weather())
    print("\n24-Hour Temperature Forecast:")
    print(weather.get_forecast())
