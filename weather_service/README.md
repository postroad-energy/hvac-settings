# Weather Service

This package provides a weather service API for retrieving weather data based on a given US zipcode or location. It fetches weather data from external APIs (OpenStreetMap and National Weather Service), processes the data, and can store it in a Timestream table via an internal API.

## Features
- Retrieves latitude/longitude for a given US zipcode using OpenStreetMap.
- Fetches weather observations (temperature, humidity, wind speed/direction) from the National Weather Service.
- Validates and formats weather data.
- Posts weather data to an internal API for storage in Timestream.
- Designed to be used as an AWS Lambda function.

## Usage

The main entry point is the `lambda_handler` function in `weather_api.py`. It expects an event with a `zip_code` field:

```python
from weather_service.weather_api import lambda_handler

event = {"zip_code": "15221"}
context = None  # AWS Lambda context if running in Lambda
result = lambda_handler(event, context)
print(result)
```

## Exception Logging
All exceptions are logged to a global instance exception logstream (currently prints to stdout; replace with your logging system as needed).

## Dependencies
- boto3
- urllib3
- haversine

## Configuration
- Update the internal API function name and AWS credentials as needed for your environment.

## License
See the main project license. 