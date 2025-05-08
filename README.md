# HVAC Settings and Weather Service

A Python package that provides endpoints for weather forecast and safety limits for HVAC (Heating, Ventilation, and Air Conditioning) systems in specific locations.

This package provides a weather service API for retrieving weather data based on a given US zipcode or location. It fetches weather data from external APIs (OpenStreetMap and National Weather Service), processes the data, and can store it in a Timestream table via an internal API.

## Description

This package helps manage and optimize HVAC systems by providing:
- Weather forecast data for specific locations
- Safety limits and parameters for HVAC operation
- Integration with AWS services (via boto3)
- Location-based calculations (via haversine)


## Features
- Retrieves latitude/longitude for a given US zipcode using OpenStreetMap.
- Fetches weather observations (temperature, humidity, wind speed/direction) from the National Weather Service.
- Validates and formats weather data.
- Posts weather data to an internal API for storage in Timestream.
- Designed to be used as an AWS Lambda function.

## Requirements

- Python 3.10 or higher
- Poetry for dependency management

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd hvac-settings
```

2. Install dependencies using Poetry:
```bash
poetry install
```

## Dependencies

- boto3: AWS SDK for Python
- urllib3: HTTP client
- haversine: Calculate distances between geographic coordinates

## Usage

[Add specific usage examples and API documentation here]

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Adhithyan Sakthivelu (admkr.2010@gmail.com) 