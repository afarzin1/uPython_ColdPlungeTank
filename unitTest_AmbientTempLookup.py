import requests, json

#OpenWeather Authentication
weather_api_key = '8d39bb994768bab0ecc03fe6a16c453a'
lat = 39.444151 
lon = -119.735969

def get_current_ambient_temperature(api_key, lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        current_temperature = data['main']['feels_like']
        return current_temperature
    else:
        return f"Error: {response.status_code}"
    
print(get_current_ambient_temperature(weather_api_key,lat,lon))