"""
AWS Lambda function handler for HVAC weather settings.
"""
import json
import boto3
from hvac_settings.weather import WeatherForecast

# Constants for AWS Lambda
FUNCTION_NAME = "localtest-internalapi-srv"
HTTP_STATUS_CODE = 202

def post_to_timestream(weather_data: dict) -> bool:
    """
    Post weather data to AWS Timestream via Lambda.
    
    Args:
        weather_data (dict): Weather data to post
        
    Returns:
        bool: True if successful, False otherwise
    """
    data = {
        "action": "set",
        "properties": {
            "table": "weather",
            "data": {
                "resource_id": str(weather_data["resource_id"]),
                "temperature": float(weather_data["temperature"]),
                "humidity": float(weather_data["humidity"]),
                "wind_speed": float(weather_data["wind_speed"]),
                "wind_direction": float(weather_data["wind_direction"]),
                "solar": 0.0
            }
        }
    }
    
    session = boto3.session.Session()
    lambda_client = session.client(
        "lambda",
        "us-east-1",
        endpoint_url="https://localhost.localstack.cloud:4566",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    
    response = lambda_client.invoke(
        FunctionName=FUNCTION_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(data)
    )
    
    return response["ResponseMetadata"]["HTTPStatusCode"] == HTTP_STATUS_CODE

def lambda_handler(event, context):
    """
    AWS Lambda function handler for weather data.
    
    Args:
        event (dict): Lambda event data
        context (object): Lambda context
        
    Returns:
        dict: Response with status code and message
    """
    try:
        # Get zip code from event, default to "15221" if not provided
        zip_code = event.get("zip_code", "15221")
        
        # Create WeatherForecast instance with zip code
        forecast = WeatherForecast(zip_code=zip_code)
        
        # Get weather data
        weather_data = forecast.get_forecast()
        
        # Post to Timestream
        success = post_to_timestream(weather_data)
        
        if success:
            return {
                'statusCode': 202,
                'body': json.dumps("Success! Weather data was posted to timestream!")
            }
        else:
            return {
                'statusCode': 202,
                'body': json.dumps("Error! Could not post to timestream!")
            }
            
    except ValueError as e:
        return {
            'statusCode': 400,
            'body': json.dumps(str(e))
        }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps(f"An unexpected error occurred: {str(e)}")
        } 