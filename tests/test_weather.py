"""
Tests for the WeatherForecast class.
"""
import json
from unittest.mock import patch, MagicMock
import pytest
from hvac_settings.weather import WeatherForecast
from datetime import datetime, timedelta
import pytz

# Mock data
MOCK_COORDINATES = [{
    "lat": "40.7128",
    "lon": "-74.0060"
}]

MOCK_METADATA = {
    "properties": {
        "gridId": "OKX",
        "gridX": 32,
        "gridY": 34,
        "observationStations": "https://api.weather.gov/stations/KNYC"
    }
}

MOCK_STATIONS = {
    "features": [{
        "properties": {
            "stationIdentifier": "KNYC"
        },
        "geometry": {
            "coordinates": [-74.0060, 40.7128]
        }
    }]
}

MOCK_WEATHER_DATA = {
    "properties": {
        "temperature": {"value": 20.0},
        "windDirection": {"value": 180},
        "windSpeed": {"value": 10.0},
        "relativeHumidity": {"value": 65.0}
    }
}

# Create mock hourly forecast data with current time
current_time = datetime.now(pytz.UTC)
MOCK_HOURLY_FORECAST = {
    "properties": {
        "periods": [
            {
                "startTime": (current_time + timedelta(hours=1)).isoformat(),
                "temperature": 72,
                "windSpeed": "10 mph",
                "windDirection": "NW",
                "shortForecast": "Sunny",
                "detailedForecast": "Sunny with light winds",
                "relativeHumidity": {"value": 45},
                "probabilityOfPrecipitation": {"value": 0},
                "isDaytime": True
            },
            {
                "startTime": (current_time + timedelta(hours=2)).isoformat(),
                "temperature": 74,
                "windSpeed": "12 mph",
                "windDirection": "NW",
                "shortForecast": "Sunny",
                "detailedForecast": "Sunny with moderate winds",
                "relativeHumidity": {"value": 42},
                "probabilityOfPrecipitation": {"value": 0},
                "isDaytime": True
            }
        ]
    }
}

@pytest.fixture
def mock_requests():
    """Mock HTTP requests."""
    with patch('urllib3.PoolManager') as mock_pool:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_pool.return_value.request.return_value = mock_response
        yield mock_pool

def test_initialization_with_coordinates():
    """Test initialization with coordinates."""
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    assert forecast.latitude == 40.7128
    assert forecast.longitude == -74.0060

def test_initialization_with_zip_code(mock_requests):
    """Test initialization with zip code."""
    mock_requests.return_value.request.return_value.data = json.dumps(MOCK_COORDINATES).encode()
    forecast = WeatherForecast(zip_code="10001")
    assert forecast.latitude == 40.7128
    assert forecast.longitude == -74.0060

def test_initialization_with_invalid_zip_code(mock_requests):
    """Test initialization with invalid zip code."""
    mock_requests.return_value.request.return_value.data = json.dumps([]).encode()
    with pytest.raises(ValueError, match="Could not get coordinates for zip code 99999"):
        WeatherForecast(zip_code="99999")

def test_initialization_with_no_parameters():
    """Test initialization with no parameters."""
    with pytest.raises(ValueError, match="Either zip_code or both latitude and longitude must be provided"):
        WeatherForecast()

def test_get_current_weather_success(mock_requests):
    """Test successful current weather retrieval."""
    # Set up mock responses in sequence
    mock_requests.return_value.request.side_effect = [
        MagicMock(status=200, data=json.dumps(MOCK_METADATA).encode()),
        MagicMock(status=200, data=json.dumps(MOCK_STATIONS).encode()),
        MagicMock(status=200, data=json.dumps(MOCK_WEATHER_DATA).encode())
    ]
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    weather_data = forecast.get_current_weather()
    
    assert isinstance(weather_data, dict)
    assert "temperature" in weather_data
    assert "humidity" in weather_data
    assert "wind_speed" in weather_data
    assert "wind_direction" in weather_data
    assert "resource_id" in weather_data
    
    # Verify temperature conversion (C to F)
    assert weather_data["temperature"] == 68.0  # (20.0 * 9/5) + 32
    
    # Verify wind speed conversion (km/h to mph)
    assert weather_data["wind_speed"] == 6.22  # 10.0 / 1.609

def test_get_current_weather_metadata_failure(mock_requests):
    """Test current weather retrieval with metadata failure."""
    mock_requests.return_value.request.return_value.status = 404
    mock_requests.return_value.request.return_value.data = json.dumps({"detail": "Not Found"}).encode()
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    with pytest.raises(ValueError, match="Could not get weather metadata"):
        forecast.get_current_weather()

def test_get_current_weather_stations_failure(mock_requests):
    """Test current weather retrieval with stations failure."""
    # First request succeeds (metadata), second fails (stations)
    mock_requests.return_value.request.side_effect = [
        MagicMock(status=200, data=json.dumps(MOCK_METADATA).encode()),
        MagicMock(status=404, data=json.dumps({"detail": "Not Found"}).encode())
    ]
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    with pytest.raises(ValueError, match="Could not get observation stations"):
        forecast.get_current_weather()

def test_get_current_weather_no_valid_data(mock_requests):
    """Test current weather retrieval with no valid station data."""
    # First two requests succeed (metadata and stations), third fails (weather data)
    mock_requests.return_value.request.side_effect = [
        MagicMock(status=200, data=json.dumps(MOCK_METADATA).encode()),
        MagicMock(status=200, data=json.dumps(MOCK_STATIONS).encode()),
        MagicMock(status=404, data=json.dumps({"detail": "Not Found"}).encode())
    ]
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    with pytest.raises(ValueError, match="Could not get valid weather data"):
        forecast.get_current_weather()

def test_get_grid_coordinates(mock_requests):
    """Test getting grid coordinates."""
    mock_requests.return_value.request.return_value.data = json.dumps(MOCK_METADATA).encode()
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    forecast._get_grid_coordinates()
    
    assert forecast.grid_id == "OKX"
    assert forecast.grid_x == 32
    assert forecast.grid_y == 34

def test_get_grid_coordinates_failure(mock_requests):
    """Test grid coordinates retrieval failure."""
    mock_requests.return_value.request.return_value.status = 404
    mock_requests.return_value.request.return_value.data = json.dumps({"detail": "Not Found"}).encode()
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    with pytest.raises(ValueError, match="Could not get weather metadata"):
        forecast._get_grid_coordinates()

def test_get_forecast_hourly_success(mock_requests):
    """Test successful hourly forecast retrieval."""
    # Mock grid coordinates request
    mock_requests.return_value.request.side_effect = [
        MagicMock(status=200, data=json.dumps(MOCK_METADATA).encode()),
        MagicMock(status=200, data=json.dumps(MOCK_HOURLY_FORECAST).encode())
    ]
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    forecast_data = forecast.get_forecast(hours=2)
    
    assert isinstance(forecast_data, dict)
    assert "hourly_forecasts" in forecast_data
    assert "generated_at" in forecast_data
    assert "hours_forecast" in forecast_data
    assert "location" in forecast_data
    
    hourly_forecasts = forecast_data["hourly_forecasts"]
    assert len(hourly_forecasts) == 2
    
    # Check first hour forecast
    first_hour = hourly_forecasts[0]
    assert first_hour["hour"] == 1  # First hour ahead
    assert first_hour["temperature"] == 72
    assert first_hour["humidity"] == 45
    assert first_hour["is_daytime"] is True
    
    # Check second hour forecast
    second_hour = hourly_forecasts[1]
    assert second_hour["hour"] == 2  # Second hour ahead
    assert second_hour["temperature"] == 74
    assert second_hour["humidity"] == 42
    assert second_hour["is_daytime"] is True

def test_get_forecast_hourly_invalid_hours():
    """Test hourly forecast with invalid hours parameter."""
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    
    with pytest.raises(ValueError, match="Hours must be between 1 and 156"):
        forecast.get_forecast(hours=0)
    
    with pytest.raises(ValueError, match="Hours must be between 1 and 156"):
        forecast.get_forecast(hours=157)

def test_get_forecast_hourly_failure(mock_requests):
    """Test hourly forecast retrieval failure."""
    # Mock successful grid coordinates request
    mock_requests.return_value.request.side_effect = [
        MagicMock(status=200, data=json.dumps(MOCK_METADATA).encode()),
        MagicMock(status=404, data=json.dumps({"detail": "Not Found"}).encode())
    ]
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    with pytest.raises(ValueError, match="Could not get forecast data"):
        forecast.get_forecast()

def test_get_forecast_hourly_no_data(mock_requests):
    """Test hourly forecast with no forecast data available."""
    # Mock successful grid coordinates request
    mock_requests.return_value.request.side_effect = [
        MagicMock(status=200, data=json.dumps(MOCK_METADATA).encode()),
        MagicMock(status=200, data=json.dumps({"properties": {"periods": []}}).encode())
    ]
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    with pytest.raises(ValueError, match="Could not find forecasts for the next 24 hours"):
        forecast.get_forecast()

def test_get_forecast_hourly_timezone_handling(mock_requests):
    """Test hourly forecast timezone handling."""
    # Mock grid coordinates request
    mock_requests.return_value.request.side_effect = [
        MagicMock(status=200, data=json.dumps(MOCK_METADATA).encode()),
        MagicMock(status=200, data=json.dumps(MOCK_HOURLY_FORECAST).encode())
    ]
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    forecast_data = forecast.get_forecast(hours=2)
    
    # Verify that generated_at is timezone-aware
    generated_at = datetime.fromisoformat(forecast_data["generated_at"])
    assert generated_at.tzinfo is not None
    
    # Verify that forecast times are timezone-aware
    for forecast in forecast_data["hourly_forecasts"]:
        forecast_time = datetime.fromisoformat(forecast["time"].replace("Z", "+00:00"))
        assert forecast_time.tzinfo is not None 