import boto3
import json
import urllib3
from urllib3 import Retry
import time
import haversine
from haversine import Unit

# url for openstreetmap to retrieve latitude/longitude coordinates
open_street_map = "https://nominatim.openstreetmap.org/search.php?country=US&postalcode="
lat_lon_format = "&format=jsonv2"
# base national weather service url to get metadata about a given latitude/longitude
nwc_points_base_url = "https://api.weather.gov/points/"
# base national weather service url to get a list of observation stations.
station_base_url = "https://api.weather.gov/stations/"
# returns the latest weather observation for a station
station_latest = "/observations/latest"
# successful status code
success = 200
# used to convert celsius to fahrenheit
fahrenheit = 9/5
thirty_two = 32
# convert to 2 decimal places for float numbers
two_dec_places = "%.2f"
# convert to 4 decimal places for float numbers
four_dec_places = "%.4f"
# used to convert wind speed from kilometers per hour to miles per hour
miles_per_hour = 1.609
# to determine limit an observation station should be within a specific zip code
radius_limit = 15.00
# error status codes
error_status_code = 400
# internal api
function_name = "localtest-internalapi-srv"
# response from internal-api
http_status_code = 202


def global_instance_exception_logstream(status, error_message):
    # TODO: shall catch any exceptions of this process and log them to a
    # global instance exception logstream
    print(str(status) + ": " + error_message)


def get_requests(url):
    data = None
    retries = Retry(connect=3, status=2)
    headers = {'User-Agent': 'sampleWeatherAPI.com'}
    try:
        http = urllib3.PoolManager()
        response = http.request("GET", url, headers=headers, retries=retries)
        if (response.status == success):
            data = json.loads(response.data)
        else:
            error_info = json.loads(response.data)
            status_code = error_info.get("status", error_status_code)
            detail = error_info.get("detail", "Unknown error")
            global_instance_exception_logstream(status_code, str(detail))
    except urllib3.exceptions.HTTPError as e:
        global_instance_exception_logstream(error_status_code, str(e))
    except Exception as e:
        global_instance_exception_logstream(error_status_code, str(e))
    return data


def validate_and_format_weather_data(station_id, zip_code):
    observation_station_full_url = station_base_url+station_id+station_latest
    latest_observation_data = get_requests(observation_station_full_url)
    if (latest_observation_data is None):
        return None
    temperature = latest_observation_data["properties"]["temperature"]["value"]
    if (temperature is None):
        global_instance_exception_logstream(
            error_status_code, f"Temperature is null for {zip_code}")
        return None
    wind_direction = latest_observation_data["properties"]["windDirection"]["value"]
    if (wind_direction is None):
        global_instance_exception_logstream(
            error_status_code, f"Wind Direction is null for {zip_code}")
        return None
    wind_speed = latest_observation_data["properties"]["windSpeed"]["value"]
    if (wind_speed is None):
        global_instance_exception_logstream(
            error_status_code, f"Wind Speed is null for {zip_code}")
        return None
    relative_humidity = latest_observation_data["properties"]["relativeHumidity"]["value"]
    if (relative_humidity is None):
        global_instance_exception_logstream(
            error_status_code, f"Relative Humidity is null for {zip_code}")
        return None
    curr_time = int(time.time() * 1000)
    temperature = (temperature * fahrenheit) + thirty_two
    temperature = two_dec_places % temperature
    wind_speed = wind_speed / miles_per_hour
    wind_speed = two_dec_places % wind_speed
    relative_humidity = two_dec_places % relative_humidity
    data = {"resource_id": curr_time, "temperature": temperature,
            "humidity": relative_humidity, "wind_speed": wind_speed,
            "wind_direction": wind_direction}
    return data


def lambda_handler(event, context):
    zip_code = event.get("zip_code", "15221")
    zip_code_url = open_street_map+zip_code+lat_lon_format
    coordinates_results = get_requests(zip_code_url)
    if (coordinates_results is None):
        return {
            'statusCode': error_status_code,
            'body': json.dumps(f"Could not connect or retrieve data from openstreetmap for zip code {zip_code}")
        }
    latitude = four_dec_places % float(coordinates_results[0]["lat"])
    longitude = four_dec_places % float(coordinates_results[0]["lon"])
    coordinates = latitude+","+longitude
    nwc_points_full_url = nwc_points_base_url+coordinates
    metadata = get_requests(nwc_points_full_url)
    if (metadata is None):
        return {
            'statusCode': error_status_code,
            'body': json.dumps(f"national weather service api for zip code {zip_code}")
        }
    observation_url = metadata["properties"]["observationStations"]
    observation_stations = get_requests(observation_url)
    if (observation_stations is None):
        return {
            'statusCode': error_status_code,
            'body': json.dumps(f"Could not retrieve list of observation stations from the national weather service api for zip code {zip_code}")
        }
    list_of_station_id = observation_stations["features"]
    obs_index = 0
    station_id = list_of_station_id[obs_index]["properties"]["stationIdentifier"]
    current_weather_data = validate_and_format_weather_data(
        station_id, zip_code)
    latitude = float(latitude)
    longitude = float(longitude)
    total_index = len(list_of_station_id)
    while ((current_weather_data is None) and ((obs_index + 1) < total_index)):
        obs_index = obs_index + 1
        obs_coordinates = list_of_station_id[obs_index]["geometry"]["coordinates"]
        nearby_zip_code_coordinates = (
            obs_coordinates[1], abs(obs_coordinates[0]))
        zip_code_coordinates = (latitude, abs(longitude))
        actual_distance = haversine.haversine(nearby_zip_code_coordinates,
                                              zip_code_coordinates, unit=Unit.KILOMETERS)
        if (actual_distance > radius_limit):
            break
        station_id = list_of_station_id[obs_index]["properties"]["stationIdentifier"]
        current_weather_data = validate_and_format_weather_data(
            station_id, zip_code)
    if (current_weather_data is None):
        return {
            'statusCode': error_status_code,
            'body': json.dumps(f"Could not retrieve valid weather data for zip code {zip_code}")
        }
    weather_data = {
        "action": "set",
        "properties": {
            "table": "weather",
            "data": {
                "resource_id": str(current_weather_data["resource_id"]),
                "temperature": float(current_weather_data["temperature"]),
                "humidity": float(current_weather_data["humidity"]),
                "wind_speed": float(current_weather_data["wind_speed"]),
                "wind_direction": float(current_weather_data["wind_direction"]),
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
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(weather_data)
    )
    if (response["ResponseMetadata"]["HTTPStatusCode"] == http_status_code):
        return {
            'statusCode': http_status_code,
            'body': json.dumps("Success! Weather data was posted to timestream!")
        }
    else:
        return {
            'statusCode': http_status_code,
            'body': json.dumps("Error! Could not post to timestream!")
        } 