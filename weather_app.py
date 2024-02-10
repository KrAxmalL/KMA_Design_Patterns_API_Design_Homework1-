import datetime
import json

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>Design Patterns and API Design. Homework 1</h2></p>"


API_TOKEN = ""  # Initially left empty
REQUESTER_NAME_FIELD = "requester_name"
LOCATION_FIELD = "location"
DATE_FIELD = "date"
TIMESTAMP_FIELD = "timestamp"
WEATHER_FIELD = "weather"


@app.route("/api/v1/weather", methods=["POST"])
def weather_endpoint():
    json_data = request.get_json()

    validate_token(json_data)

    requester_name = extract_string(REQUESTER_NAME_FIELD, json_data)
    location = extract_string(LOCATION_FIELD, json_data)
    date = extract_string(DATE_FIELD, json_data)

    weather = get_weather(location, date)
    return {
        REQUESTER_NAME_FIELD: requester_name,
        LOCATION_FIELD: location,
        DATE_FIELD: date,
        TIMESTAMP_FIELD: current_timestamp(),
        WEATHER_FIELD: build_weather_response(weather)
    }


VISUAL_CROSSING_API_KEY = ""  # Initially left empty
VISUAL_CROSSING_BASE_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
VISUAL_CROSSING_KEY_QUERY_PARAM = "key"
VISUAL_CROSSING_LANG_QUERY_PARAM = "lang"
VISUAL_CROSSING_LANG_VALUE = "en"
VISUAL_CROSSING_MEASUREMENT_UNIT_QUERY_PARAM = "unitGroup"
VISUAL_CROSSING_MEASUREMENT_UNIT_VALUE = "metric"


def get_weather(location, date):
    url = f"{VISUAL_CROSSING_BASE_URL}/{location}/{date}" \
          f"?{VISUAL_CROSSING_KEY_QUERY_PARAM}={VISUAL_CROSSING_API_KEY}" \
          f"&{VISUAL_CROSSING_MEASUREMENT_UNIT_QUERY_PARAM}={VISUAL_CROSSING_MEASUREMENT_UNIT_VALUE}" \
          f"&{VISUAL_CROSSING_LANG_QUERY_PARAM}={VISUAL_CROSSING_LANG_VALUE}"

    response = requests.get(url)
    if response.status_code == requests.codes.ok:
        return json.loads(response.text)
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)


def validate_token(json_data):
    token = json_data.get("token")
    if token is None:
        raise InvalidUsage("Field 'token' must be present", status_code=requests.codes.bad_request)
    elif token != API_TOKEN:
        raise InvalidUsage("Wrong API token", status_code=requests.codes.forbidden)


def extract_string(key, json_data):
    value = json_data.get(key)
    if value is None or not value or not value.strip():
        raise InvalidUsage(f"Field '{key}' must be present and not empty", status_code=requests.codes.bad_request)
    return value


def current_timestamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def build_weather_response(weather):
    current_day = weather.get("days")[0]  # array of days contains only one value - for day from the request

    # Units of measurement for different fields
    # Temperature - degrees celcius
    # Humidity and cloud coverage - percents
    # Pressure - millibars
    # Wind speed - kilometres per hour
    # Sunrise and sunset time is specified in timezone of the requested location
    return {
        "description": current_day.get("description"),
        "conditions": current_day.get("conditions"),
        "average_temperature_c": current_day.get("temp"),
        "average_temperature_feels_like_c": current_day.get("feelslike"),
        "max_temperature_c": current_day.get("tempmax"),
        "max_temperature_feels_like_c": current_day.get("feelslikemax"),
        "min_temperature_c": current_day.get("tempmin"),
        "min_temperature_feels_like_c": current_day.get("feelslikemin"),
        "pressure_mb": current_day.get("pressure"),
        "humidity_p": current_day.get("humidity"),
        "cloud_coverage_p": current_day.get("cloudcover"),
        "wind_speed_kph": current_day.get("windspeed"),
        "sunrise_time": current_day.get("sunrise"),
        "sunset_time": current_day.get("sunset")
    }
