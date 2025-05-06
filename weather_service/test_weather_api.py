import unittest
from weather_service.weather_api import lambda_handler

class TestWeatherAPI(unittest.TestCase):
    def test_lambda_handler_with_valid_zip(self):
        event = {"zip_code": "15221"}
        context = None
        result = lambda_handler(event, context)
        self.assertIn('statusCode', result)
        self.assertIn('body', result)

if __name__ == "__main__":
    unittest.main() 