
import openmeteo_requests
import json
import requests_cache
import pandas as pd
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"



# Coordinates for each location
coordinates = [
    {"latitude": 46.6005922, "longitude": 11.7257836},  # Seceda (Val Gardena)
    {"latitude": 47.2140108, "longitude": 10.1167400},  # Lech (Vorarlberg)
    {"latitude": 47.3737011, "longitude": 13.7786600},  # Hauser Kaibling (Schladming)
    {"latitude": 45.2979108, "longitude": 6.5822692},   # Val Thorens (French alps)
    {"latitude": 46.7723989, "longitude": 9.8493406},   # Davos
    {"latitude": 46.6184408, "longitude": 8.5983633},   # Andermatt
    {"latitude": 45.4556342, "longitude": 6.9202936},   # Tignes and Val-d'Isère
    {"latitude": 45.9339119, "longitude": 6.8378342},   # Chamonix (Brévent)
    {"latitude": 45.9988231, "longitude": 7.7669625},   # Cervinia
     {"latitude": 45.9938758, "longitude": 7.7550900},   # Zarmatt
    {"latitude": 47.2514939, "longitude": 11.9826003},  # Kitzbuhel
]

# Define names for each location
location_names = [
    "Seceda (Val Gardena)", "Lech (Vorarlberg)", "Hauser Kaibling (Schladming)", "Val Thorens (French alps)", "Davos", 
    "Andermatt", "Tignes and Val-d'Isere", "Chamonix (Brevent)", "Cervinia", "Zermatt", "Kitzbuhel"
]

# Common parameters
common_params = {
    "daily": ["temperature_2m_max", "apparent_temperature_max", "snowfall_sum", "precipitation_sum", "sunshine_duration",
              "rain_sum","precipitation_hours","wind_speed_10m_max"],
    "timezone": "Europe/Berlin"
}

output = {location: {
    "temperature_2m_max": [],
    "apparent_temperature_max": [],
    "snowfall_sum": [],
    "precipitation_sum": [],
    "sunshine_duration": [],
    "rain_sum": [],
    "precipitation_hours": [],
    "wind_speed_10m_max": []
} for location in location_names}


# Loop through each location and make the request
for index, coord in enumerate(coordinates):
    params = {
        "latitude": coord["latitude"],
        "longitude": coord["longitude"],
        "daily": common_params["daily"],  # Use lowercase 'daily'
        "timezone": common_params["timezone"]
    }
    
    try:
        response = openmeteo.weather_api(url, params=params)
        
       
        
        # Access the first element of the response list
        weather_response = response[0]  # Get the WeatherApiResponse object

        
    
        # Print the structure of the weather_response to inspect its attributes
        print(f"Response structure for {location_names[index]}: {dir(weather_response)}")

        print(f"Location: {location_names[index]}")
        print(f"Coordinates: {coord['latitude']}°N, {coord['longitude']}°E")
        
      
        
        location = location_names[index]
       
        # Access the daily data correctly
        daily = weather_response.Daily()
        if daily:
             output[location]['temperature_2m_max'] = daily.Variables(0).ValuesAsNumpy().tolist()
             output[location]['apparent_temperature_max'] = daily.Variables(1).ValuesAsNumpy().tolist()
             output[location]['sunshine_duration'] = daily.Variables(2).ValuesAsNumpy().tolist()
             output[location]['precipitation_sum'] = daily.Variables(3).ValuesAsNumpy().tolist()
             output[location]['rain_sum'] = daily.Variables(4).ValuesAsNumpy().tolist()
             output[location]['snowfall_sum'] = daily.Variables(5).ValuesAsNumpy().tolist()
             output[location]['precipitation_hours'] = daily.Variables(6).ValuesAsNumpy().tolist()
             output[location]['wind_speed_10m_max'] = daily.Variables(7).ValuesAsNumpy().tolist()
        else:
            print("No daily data available.")

        print("\n")
       
        
    except Exception as e:  # Catch all exceptions
        print(f"Error fetching data for {location_names[index]}: {e}")
        
        
        
print(json.dumps(output, indent=4))

with open('weather_data.json', 'w') as file:
    json.dump(output, file, indent=4)