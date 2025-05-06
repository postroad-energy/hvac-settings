"""
Tests for the WeatherForecast class.
"""
import json
from unittest.mock import patch, MagicMock
import pytest
from hvac_settings.weather import WeatherForecast

# Mock data
MOCK_COORDINATES = [{
    "lat": "40.7128",
    "lon": "-74.0060"
}]

MOCK_METADATA = {
    "properties": {
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

def test_get_forecast_success(mock_requests):
    """Test successful weather forecast retrieval."""
    # Set up mock responses in sequence
    mock_requests.return_value.request.side_effect = [
        MagicMock(status=200, data=json.dumps(MOCK_METADATA).encode()),
        MagicMock(status=200, data=json.dumps(MOCK_STATIONS).encode()),
        MagicMock(status=200, data=json.dumps(MOCK_WEATHER_DATA).encode())
    ]
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    weather_data = forecast.get_forecast()
    
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

def test_get_forecast_metadata_failure(mock_requests):
    """Test weather forecast retrieval with metadata failure."""
    mock_requests.return_value.request.return_value.status = 404
    mock_requests.return_value.request.return_value.data = json.dumps({"detail": "Not Found"}).encode()
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    with pytest.raises(ValueError, match="Could not get weather metadata"):
        forecast.get_forecast()

def test_get_forecast_stations_failure(mock_requests):
    """Test weather forecast retrieval with stations failure."""
    # Mock successful metadata request
    mock_requests.return_value.request.return_value.data = json.dumps(MOCK_METADATA).encode()
    
    # Mock failed stations request
    mock_requests.return_value.request.return_value.status = 404
    mock_requests.return_value.request.return_value.data = json.dumps({"detail": "Not Found"}).encode()
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    
    # First request succeeds (metadata), second fails (stations)
    mock_requests.return_value.request.side_effect = [
        MagicMock(status=200, data=json.dumps(MOCK_METADATA).encode()),
        MagicMock(status=404, data=json.dumps({"detail": "Not Found"}).encode())
    ]
    
    with pytest.raises(ValueError, match="Could not get observation stations"):
        forecast.get_forecast()

def test_get_forecast_no_valid_data(mock_requests):
    """Test weather forecast retrieval with no valid station data."""
    # Mock successful metadata request
    mock_requests.return_value.request.return_value.data = json.dumps(MOCK_METADATA).encode()
    
    # Mock successful stations request
    mock_requests.return_value.request.return_value.data = json.dumps(MOCK_STATIONS).encode()
    
    # Mock failed weather data request
    mock_requests.return_value.request.return_value.status = 404
    mock_requests.return_value.request.return_value.data = json.dumps({"detail": "Not Found"}).encode()
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    
    # First two requests succeed (metadata and stations), third fails (weather data)
    mock_requests.return_value.request.side_effect = [
        MagicMock(status=200, data=json.dumps(MOCK_METADATA).encode()),
        MagicMock(status=200, data=json.dumps(MOCK_STATIONS).encode()),
        MagicMock(status=404, data=json.dumps({"detail": "Not Found"}).encode())
    ]
    
    with pytest.raises(ValueError, match="Could not get valid weather data"):
        forecast.get_forecast()

def test_validate_and_format_weather_data_missing_fields(mock_requests):
    """Test weather data validation with missing fields."""
    mock_requests.return_value.request.return_value.data = json.dumps({
        "properties": {
            "temperature": {"value": None},
            "windDirection": {"value": 180},
            "windSpeed": {"value": 10.0},
            "relativeHumidity": {"value": 65.0}
        }
    }).encode()
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    result = forecast._validate_and_format_weather_data("KNYC", "10001")
    assert result is None

def test_validate_and_format_weather_data_success(mock_requests):
    """Test successful weather data validation and formatting."""
    mock_requests.return_value.request.return_value.data = json.dumps(MOCK_WEATHER_DATA).encode()
    
    forecast = WeatherForecast(latitude=40.7128, longitude=-74.0060)
    result = forecast._validate_and_format_weather_data("KNYC", "10001")
    
    assert isinstance(result, dict)
    assert "temperature" in result
    assert "humidity" in result
    assert "wind_speed" in result
    assert "wind_direction" in result
    assert "resource_id" in result
    
    # Verify temperature conversion (C to F)
    assert result["temperature"] == 68.0  # (20.0 * 9/5) + 32
    
    # Verify wind speed conversion (km/h to mph)
    assert result["wind_speed"] == 6.22  # 10.0 / 1.609 