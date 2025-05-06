import json
from weather_service.weather_api import lambda_handler as weather_lambda_handler

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    # Check if this is a Lambda URL/API Gateway invocation
    if 'requestContext' in event and 'http' in event['requestContext']:
        # Lambda URL invocation
        requested_path = event.get('rawPath', '/')
        if event['requestContext']['http']['method'] == 'POST':
            body = json.loads(event.get('body', '{}'))
            zip_code = body.get("zip_code")
            location = body.get("location")
            # Pass zip_code or location to the weather lambda handler
            weather_event = {}
            if zip_code:
                weather_event["zip_code"] = zip_code
            if location:
                weather_event["location"] = location
            response = weather_lambda_handler(weather_event, context)
            return response
        else:
            # For GET or other methods, return usage info
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "expected_payload": {"zip_code": "15221"}
                })
            }
    else:
        # Direct Lambda invocation
        return weather_lambda_handler(event, context) 