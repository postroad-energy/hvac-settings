"""
Safety limits module for HVAC settings.
"""

class SafetyLimits:
    def __init__(self, min_temp: float, max_temp: float):
        """
        Initialize SafetyLimits with temperature range.
        
        Args:
            min_temp (float): Minimum safe temperature
            max_temp (float): Maximum safe temperature
            
        Raises:
            ValueError: If min_temp is greater than max_temp
        """
        if min_temp > max_temp:
            raise ValueError("Minimum temperature cannot be greater than maximum temperature")
        
        self.min_temp = min_temp
        self.max_temp = max_temp
    
    def is_safe_temperature(self, temperature: float) -> bool:
        """
        Check if a given temperature is within safe limits.
        
        Args:
            temperature (float): Temperature to check
            
        Returns:
            bool: True if temperature is within safe limits, False otherwise
        """
        return self.min_temp <= temperature <= self.max_temp 