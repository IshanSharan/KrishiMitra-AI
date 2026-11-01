
import requests


def get_coordinates(city):

    url = "https://geocoding-api.open-meteo.com/v1/search"

    params = {
        "name": city,
        "count": 5,
        "language": "en",
        "format": "json",
        "countryCode": "IN"
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()

    data = response.json()

    if not data.get("results"):
        raise ValueError("Location not found")

    return data["results"][0]


def get_weather(city):

    location = get_coordinates(city)

    latitude = location["latitude"]
    longitude = location["longitude"]

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m"
        ],

        "daily": [
            "precipitation_sum",
            "precipitation_probability_max",
            "temperature_2m_max",
            "temperature_2m_min"
        ],

        "forecast_days": 3,
        "timezone": "auto"
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()

    weather_data = response.json()

    return {
        "location": location["name"],
        "state": location.get("admin1", "Unknown"),
        "latitude": latitude,
        "longitude": longitude,
        "current": weather_data["current"],
        "daily": weather_data["daily"]
    }
