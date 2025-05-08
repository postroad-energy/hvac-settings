"""
Safety limits module for HVAC settings.
"""
from hvac_settings.weather import WeatherForecast
import math

class SafetyLimits:
    def __init__(self, zip_code: str):
        """
        Initialize SafetyLimits with zip code to get weather data.
        
        Args:
            zip_code (str): US zip code for weather data
            
        Raises:
            ValueError: If weather data cannot be retrieved
        """
        self.weather = WeatherForecast(zip_code=zip_code)
        self._update_weather_data()
    
    def _update_weather_data(self) -> None:
        """Update current weather data."""
        self.current_weather = self.weather.get_current_weather()
        self.forecast = self.weather.get_forecast(hours=1)
    
    def _calculate_heat_index(self, temperature: float, humidity: float) -> float:
        """
        Calculate heat index using the Rothfusz regression.
        
        Args:
            temperature (float): Temperature in Fahrenheit
            humidity (float): Relative humidity percentage
            
        Returns:
            float: Heat index in Fahrenheit
        """
        # Constants for heat index calculation
        c1 = -42.379
        c2 = 2.04901523
        c3 = 10.14333127
        c4 = -0.22475541
        c5 = -6.83783e-3
        c6 = -5.481717e-2
        c7 = 1.22874e-3
        c8 = 8.5282e-4
        c9 = -1.99e-6
        
        # Calculate heat index
        hi = (c1 + (c2 * temperature) + (c3 * humidity) + 
              (c4 * temperature * humidity) + (c5 * temperature**2) + 
              (c6 * humidity**2) + (c7 * temperature**2 * humidity) + 
              (c8 * temperature * humidity**2) + (c9 * temperature**2 * humidity**2))
        
        # Adjustments for very low and very high temperatures
        if temperature < 80 or humidity < 40:
            hi = temperature
        
        return round(hi, 1)
    
    def _calculate_wind_chill(self, temperature: float, wind_speed: float) -> float:
        """
        Calculate wind chill using the new wind chill formula.
        
        Args:
            temperature (float): Temperature in Fahrenheit
            wind_speed (float): Wind speed in mph
            
        Returns:
            float: Wind chill in Fahrenheit
        """
        if temperature > 50 or wind_speed < 3:
            return temperature
            
        wc = 35.74 + (0.6215 * temperature) - (35.75 * (wind_speed ** 0.16)) + \
             (0.4275 * temperature * (wind_speed ** 0.16))
        
        return round(wc, 1)
    
    def get_adjusted_temperature_limits(self) -> dict:
        """
        Calculate humidity and wind-adjusted temperature limits.
        
        Returns:
            dict: Dictionary containing adjusted temperature limits and current conditions
        """
        self._update_weather_data()
        
        current_temp = self.current_weather["temperature"]
        current_humidity = self.current_weather["humidity"]
        current_wind = self.current_weather["wind_speed"]
        
        # Calculate heat index and wind chill
        heat_index = self._calculate_heat_index(current_temp, current_humidity)
        wind_chill = self._calculate_wind_chill(current_temp, current_wind)
        
        # Base safety limits (can be adjusted based on your requirements)
        base_min_temp = 68  # Minimum comfortable temperature
        base_max_temp = 78  # Maximum comfortable temperature
        
        # Adjust limits based on heat index and wind chill
        adjusted_min_temp = max(base_min_temp, wind_chill)
        adjusted_max_temp = min(base_max_temp, heat_index)
        
        return {
            "current_conditions": {
                "temperature": current_temp,
                "humidity": current_humidity,
                "wind_speed": current_wind,
                "heat_index": heat_index,
                "wind_chill": wind_chill
            },
            "adjusted_limits": {
                "min_temperature": adjusted_min_temp,
                "max_temperature": adjusted_max_temp
            }
        }
    
    def is_safe_temperature(self, temperature: float) -> bool:
        """
        Check if a given temperature is within safe limits considering humidity and wind.
        
        Args:
            temperature (float): Temperature to check
            
        Returns:
            bool: True if temperature is within safe limits, False otherwise
        """
        limits = self.get_adjusted_temperature_limits()
        return limits["adjusted_limits"]["min_temperature"] <= temperature <= limits["adjusted_limits"]["max_temperature"]

if __name__ == "__main__":
    # Example usage of SafetyLimits class
    try:
        # Initialize SafetyLimits with a zip code
        safety = SafetyLimits(zip_code="94305")
        
        # Get current conditions and adjusted temperature limits
        limits = safety.get_adjusted_temperature_limits()
        
        # Print current weather conditions
        print("\nCurrent Weather Conditions:")
        print(f"Temperature: {limits['current_conditions']['temperature']}°F")
        print(f"Humidity: {limits['current_conditions']['humidity']}%")
        print(f"Wind Speed: {limits['current_conditions']['wind_speed']} mph")
        print(f"Heat Index: {limits['current_conditions']['heat_index']}°F")
        print(f"Wind Chill: {limits['current_conditions']['wind_chill']}°F")
        
        # Print adjusted temperature limits
        print("\nAdjusted Temperature Limits:")
        print(f"Minimum Safe Temperature: {limits['adjusted_limits']['min_temperature']}°F")
        print(f"Maximum Safe Temperature: {limits['adjusted_limits']['max_temperature']}°F")
        
        # Check if some example temperatures are safe
        test_temperatures = [65, 72, 80]
        print("\nTemperature Safety Checks:")
        for temp in test_temperatures:
            is_safe = safety.is_safe_temperature(temp)
            print(f"{temp}°F is {'safe' if is_safe else 'not safe'}")
            
    except ValueError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}") 