"""
Tests for the SafetyLimits class.
"""
import pytest
from unittest.mock import patch, MagicMock
from hvac_settings.safety import SafetyLimits

# Mock weather data
MOCK_CURRENT_WEATHER = {
    "temperature": 75.0,
    "humidity": 60.0,
    "wind_speed": 5.0
}

MOCK_FORECAST = {
    "hourly_forecasts": [{
        "hour": 1,
        "temperature": 75.0,
        "humidity": 60.0
    }]
}

@pytest.fixture
def mock_weather():
    """Mock WeatherForecast class."""
    with patch('hvac_settings.safety.WeatherForecast') as mock:
        mock_instance = MagicMock()
        mock_instance.get_current_weather.return_value = MOCK_CURRENT_WEATHER
        mock_instance.get_forecast.return_value = MOCK_FORECAST
        mock.return_value = mock_instance
        yield mock_instance

def test_initialization(mock_weather):
    """Test SafetyLimits initialization."""
    safety = SafetyLimits(zip_code="94305")
    assert safety.weather is not None
    mock_weather.get_current_weather.assert_called_once()
    mock_weather.get_forecast.assert_called_once_with(hours=1)

def test_heat_index_calculation():
    """Test heat index calculation."""
    safety = SafetyLimits(zip_code="94305")
    
    # Test case 1: Normal conditions
    hi = safety._calculate_heat_index(80, 60)
    assert isinstance(hi, float)
    assert hi > 80  # Heat index should be higher than temperature
    
    # Test case 2: Low temperature (should return original temperature)
    hi = safety._calculate_heat_index(75, 60)
    assert hi == 75.0
    
    # Test case 3: Low humidity (should return original temperature)
    hi = safety._calculate_heat_index(85, 30)
    assert hi == 85.0

def test_wind_chill_calculation():
    """Test wind chill calculation."""
    safety = SafetyLimits(zip_code="94305")
    
    # Test case 1: Normal conditions
    wc = safety._calculate_wind_chill(30, 10)
    assert isinstance(wc, float)
    assert wc < 30  # Wind chill should be lower than temperature
    
    # Test case 2: High temperature (should return original temperature)
    wc = safety._calculate_wind_chill(55, 10)
    assert wc == 55.0
    
    # Test case 3: Low wind speed (should return original temperature)
    wc = safety._calculate_wind_chill(30, 2)
    assert wc == 30.0

def test_get_adjusted_temperature_limits(mock_weather):
    """Test getting adjusted temperature limits."""
    safety = SafetyLimits(zip_code="94305")
    limits = safety.get_adjusted_temperature_limits()
    
    assert isinstance(limits, dict)
    assert "current_conditions" in limits
    assert "adjusted_limits" in limits
    
    current = limits["current_conditions"]
    assert "temperature" in current
    assert "humidity" in current
    assert "wind_speed" in current
    assert "heat_index" in current
    assert "wind_chill" in current
    
    adjusted = limits["adjusted_limits"]
    assert "min_temperature" in adjusted
    assert "max_temperature" in adjusted
    assert adjusted["min_temperature"] <= adjusted["max_temperature"]

def test_is_safe_temperature(mock_weather):
    """Test temperature safety check."""
    safety = SafetyLimits(zip_code="94305")
    
    # Get the current adjusted limits
    limits = safety.get_adjusted_temperature_limits()
    min_temp = limits["adjusted_limits"]["min_temperature"]
    max_temp = limits["adjusted_limits"]["max_temperature"]
    
    # Test temperatures within and outside limits
    assert safety.is_safe_temperature((min_temp + max_temp) / 2)  # Middle of range
    assert not safety.is_safe_temperature(min_temp - 5)  # Below minimum
    assert not safety.is_safe_temperature(max_temp + 5)  # Above maximum 