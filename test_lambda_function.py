import unittest
import json
from lambda_function import lambda_handler

class TestWeatherLambdaHandler(unittest.TestCase):
    def test_post_with_valid_zip_code(self):
        event = {
            "requestContext": {"http": {"method": "POST"}},
            "body": json.dumps({"zip_code": "15221"})
        }
        context = None
        response = lambda_handler(event, context)
        self.assertIn("statusCode", response)
        self.assertIn("body", response)
        self.assertIsInstance(response["statusCode"], int)
        self.assertIsInstance(response["body"], str)

    def test_get_usage_info(self):
        event = {
            "requestContext": {"http": {"method": "GET"}},
            "rawPath": "/weather"
        }
        context = None
        response = lambda_handler(event, context)
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertIn("expected_payload", body)
        self.assertIn("zip_code", body["expected_payload"])

if __name__ == "__main__":
    unittest.main() 