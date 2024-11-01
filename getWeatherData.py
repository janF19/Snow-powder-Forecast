import openmeteo_requests
import json
import requests_cache
import logging
from retry_requests import retry

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Setup the Open-Meteo API client with cache and retry on error
CACHE_EXPIRY = 86400  # Cache expiry for 24 hours (since forecasts update daily)
cache_session = requests_cache.CachedSession('.cache', expire_after=CACHE_EXPIRY)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# API URL and common parameters
API_URL = "https://api.open-meteo.com/v1/forecast"
COMMON_PARAMS = {
    "daily": ["temperature_2m_max", "apparent_temperature_max", "snowfall_sum", "precipitation_sum",
              "sunshine_duration", "rain_sum", "precipitation_hours", "wind_speed_10m_max"],
    "timezone": "Europe/Berlin",
    "past_days": 14,
	"forecast_days": 14
}

# Coordinates and corresponding location names
locations = [
    {"name": "Seceda (Val Gardena)", "latitude": 46.6005922, "longitude": 11.7257836},
    {"name": "Lech (Vorarlberg)", "latitude": 47.2140108, "longitude": 10.1167400},
    {"name": "Hauser Kaibling (Schladming)", "latitude": 47.3737011, "longitude": 13.7786600},
    {"name": "Val Thorens (French alps)", "latitude": 45.2979108, "longitude": 6.5822692},
    {"name": "Davos", "latitude": 46.7723989, "longitude": 9.8493406},
    {"name": "Andermatt", "latitude": 46.6184408, "longitude": 8.5983633},
    {"name": "Tignes and Val-d'Isère", "latitude": 45.4556342, "longitude": 6.9202936},
    {"name": "Chamonix (Brévent)", "latitude": 45.9339119, "longitude": 6.8378342},
    {"name": "Cervinia", "latitude": 45.9988231, "longitude": 7.7669625},
    {"name": "Zermatt", "latitude": 45.9938758, "longitude": 7.7550900},
    {"name": "Kitzbuhel", "latitude": 47.442860, "longitude": 12.390110},
]

# Initialize the output data structure with elevation and snow sums
output = {loc['name']: {var: [] for var in COMMON_PARAMS['daily']} for loc in locations}
# Add elevation and snowfall sums fields
for loc in locations:
    output[loc['name']]['elevation'] = None  # Initialize elevation field
    output[loc['name']]['history14daySum'] = None # Initialize historic sum field
    output[loc['name']]['3daysSnowSum'] = None  # Initialize 3-day snow sum field
    output[loc['name']]['7daysSnowSum'] = None  # Initialize 7-day snow sum field
    output[loc['name']]['14daysSnowSum'] = None  # Initialize 7-day snow sum field
    

def fetch_weather_data(location):
    """Fetches weather data for a given location."""
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "daily": COMMON_PARAMS["daily"],
        "timezone": COMMON_PARAMS["timezone"],
        "past_days": COMMON_PARAMS["past_days"],  # Include the past_days parameter
        "forecast_days": COMMON_PARAMS["forecast_days"]  # Include the forecast_days parameter
    }
    
    try:
        response = openmeteo.weather_api(API_URL, params=params)
        weather_response = response[0]  # Extract first response object

        # Extract elevation data
        elevation = weather_response.Elevation()  # Assuming this method returns elevation value
        output[location['name']]['elevation'] = elevation  # Store elevation in the output

        # Extract daily data
        daily_data = weather_response.Daily()
        if daily_data:
            # Extract snowfall_sum data
            snowfall_sum = daily_data.Variables(COMMON_PARAMS['daily'].index('snowfall_sum')).ValuesAsNumpy().tolist()
            logging.info(f"Raw snowfall data for {location['name']}: {snowfall_sum}")
            
            if len(snowfall_sum) >= 28:
                output[location['name']]['history14daySum'] = sum(snowfall_sum[:14])
                output[location['name']]['3daysSnowSum'] = sum(snowfall_sum[14:17])
                output[location['name']]['7daysSnowSum'] = sum(snowfall_sum[14:21])
                output[location['name']]['14daysSnowSum'] = sum(snowfall_sum[14:28])
            else:
                # Handle the case where snowfall_sum is not long enough (e.g., fewer forecasted days)
                logging.warning(f"Not enough snowfall data for {location['name']}")
                output[location['name']]['history14daySum'] = None
                output[location['name']]['3daysSnowSum'] = None
                output[location['name']]['7daysSnowSum'] = None
                output[location['name']]['14daysSnowSum'] = None

            # Store daily values in the output
            for idx, var in enumerate(COMMON_PARAMS['daily']):
                output[location['name']][var] = daily_data.Variables(idx).ValuesAsNumpy().tolist()
        else:
            logging.warning(f"No daily data available for {location['name']}")
    
    except Exception as e:
        logging.error(f"Error fetching data for {location['name']}: {str(e)}")

def main():
    # Loop through each location and fetch weather data
    for location in locations:
        logging.info(f"Fetching data for {location['name']}")
        fetch_weather_data(location)
    
    # Write the output to a file
    with open('weather_data2.json', 'w') as file:
        json.dump(output, file, indent=4)
        logging.info("Weather data successfully written to 'weather_data2.json'")

if __name__ == "__main__":
    main()
