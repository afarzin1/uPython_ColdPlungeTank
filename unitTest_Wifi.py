import network,time,urequests,json

ssid = "MyNet1-guest"
password = "farzinguest"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

if not wlan.isconnected():
    while not wlan.isconnected():
        print("Trying to connect...")
        wlan.connect(ssid, password)
        time.sleep(3)
if wlan.isconnected():
    print("Connected to Wifi")
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )
def get_current_ambient_temperature(api_key, lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = urequests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        current_temperature = data['main']['feels_like']
        return current_temperature
    else:
        return f"Error: {response.status_code}"

weather_api_key = '8d39bb994768bab0ecc03fe6a16c453a'
lat = 39.444151 
lon = -119.735969

ambient_temperature = get_current_ambient_temperature(weather_api_key, lat, lon)
print(ambient_temperature)