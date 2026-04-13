#!/usr/bin/env python3
"""
Fetch historical temperature in Amiens, France on December 6, 1984 at 18h.
Uses the Open-Meteo Historical Weather API (free, no API key required).
API docs: https://open-meteo.com/en/docs/historical-weather-api
"""

import requests

# Amiens, France geographic coordinates
LATITUDE = 49.8941
LONGITUDE = 2.2958
CITY = "Amiens"
TARGET_DATE = "1984-12-06"
TARGET_HOUR = 18  # 18h local time (Europe/Paris)

API_URL = "https://archive-api.open-meteo.com/v1/archive"

params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": TARGET_DATE,
    "end_date": TARGET_DATE,
    "hourly": "temperature_2m",
    "timezone": "Europe/Paris",
}

response = requests.get(API_URL, params=params, timeout=30)
response.raise_for_status()
data = response.json()

times = data["hourly"]["time"]
temperatures = data["hourly"]["temperature_2m"]

# Find the closest data point to 18h
target_time = f"{TARGET_DATE}T{TARGET_HOUR:02d}:00"
if target_time in times:
    idx = times.index(target_time)
    temp = temperatures[idx]
    print(f"Temperature in {CITY} on {TARGET_DATE} at {TARGET_HOUR}h: {temp}°C")
else:
    # Find closest available time
    from datetime import datetime
    target_dt = datetime.fromisoformat(target_time)
    closest_idx = min(
        range(len(times)),
        key=lambda i: abs(datetime.fromisoformat(times[i]) - target_dt),
    )
    temp = temperatures[closest_idx]
    closest_time = times[closest_idx]
    print(
        f"Exact time not found. Closest data point: {closest_time} -> {temp}°C"
    )
    print(f"Temperature in {CITY} on {closest_time}: {temp}°C")
