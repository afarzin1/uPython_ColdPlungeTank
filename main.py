import time, picodebug, mySecrets
from machine import Pin
from ota import OTAUpdater

ver="1.04"
devMode = 0

print("Initializing...")
picodebug.logPrint("Initializing")

#turn on LED for first-scan
pin = Pin("LED", Pin.OUT)
pin.on()
time.sleep(2)

picodebug.logPrint("Importing libs")
import network,time,urequests,json, ntptime
import math
import machine
import blynklib
import gc

#First scan initialization
firstScan = 0
CycleLoopCounter = 0
BLYNK_AUTH = mySecrets.blynkauth

picodebug.logPrint("Initializing WIFI")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
ssid = mySecrets.mySSID
password = mySecrets.myWifiPassword

def ConnectWifi(printIP):

    attemptCounter = 0
    
    if not wlan.isconnected():
        while not wlan.isconnected():
            if attemptCounter == 5:
                picodebug.logPrint("Wifi not connecting, rebooting...")
                machine.reset()
            print("Trying to connect...")
            wlan.connect(ssid, password)
            pin.toggle()
            attemptCounter += 1
            time.sleep(3)
    if wlan.isconnected():
            
        status = wlan.ifconfig()
        if printIP:
            print("Connected to Wifi")
            print( 'ip = ' + status[0] )

def get_uptime():
    # Get the current uptime in milliseconds
    uptime_ms = time.ticks_ms()
    
    # Calculate hours, minutes, and seconds
    uptime_s = uptime_ms // 1000
    hours = uptime_s // 3600
    minutes = (uptime_s % 3600) // 60
    seconds = uptime_s % 60
    
    return "{}:{}:{}".format(hours, minutes, seconds)

def get_uptime_minutes():
    # Get the current uptime in milliseconds
    uptime_ms = time.ticks_ms()
    
    # Calculate hours, minutes, and seconds
    uptime_s = uptime_ms // 1000
    minutes = (uptime_s % 3600) // 60

    return minutes

def is_dst(time_tuple):
    # DST starts on the second Sunday in March
    dst_start = time.mktime((time_tuple[0], 3, 8, 2, 0, 0, 0, 0))
    # DST ends on the first Sunday in November
    dst_end = time.mktime((time_tuple[0], 11, 1, 2, 0, 0, 0, 0))
    
    # Find the actual DST start and end times for the current year
    while time.localtime(dst_start)[6] != 6:  # Sunday
        dst_start += 86400  # Add one day
    while time.localtime(dst_end)[6] != 6:  # Sunday
        dst_end += 86400  # Add one day
    
    current_time_seconds = time.mktime(time_tuple)
    
    return current_time_seconds >= dst_start and current_time_seconds < dst_end

def get_worldTime():
    ntptime.host = 'pool.ntp.org'
    
    try:
        ntptime.settime()

        # Initialize RTC
        rtc = machine.RTC()

        # Get the updated time
        current_time = time.localtime()

        # Convert to PST (UTC - 8 hours) or PDT (UTC - 7 hours)
        offset = -28800  # PST: 8 hours * 60 minutes/hour * 60 seconds/minute
        if is_dst(current_time):
            offset += 3600  # Add 1 hour for Daylight Saving Time

        pst_time = time.mktime(current_time) + offset
        pst_time = time.localtime(pst_time)

        # Set the RTC time
        rtc.datetime((pst_time[0], pst_time[1], pst_time[2], pst_time[6], pst_time[3], pst_time[4], pst_time[5], 0))
        time.sleep(1)
        return 1
    except:
        return 0

def get_current_ambient_temperature(api_key, lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = urequests.get(url)
    #time.sleep(2)
    if response.status_code == 200:
        data = json.loads(response.text)
        current_temperature = data['main']['feels_like']
        return current_temperature
    else:
        return f"Error: {response.status_code}"

def calculate_ice_packs(T_initial, T_final):
    m_water = 184955.685  # mass of 48.85 gallons of water in grams
    c = 4.18  # specific heat capacity of water in J/g°C
    Lf = 334  # heat of fusion for water in J/g
    m_ice_pack = 520  # mass of one ice pack in grams

    E_needed = m_water * c * (T_initial - T_final)
    E_ice_pack = m_ice_pack * (Lf + c * T_final)

    N = E_needed / E_ice_pack
    N = math.ceil(N)  # Round up to the nearest whole number
    return N

#Init Tags--------------------------------------------------
icepacks_added = ""
coolingActive = ""
waterSetpoint = ""
consoleLog = ""
ambient_temperature = ""
ErroLog = ""
EventSent_CoolingActive = 0
EventSent_CoolingActive_Off = 0
WaterTempSamples = []
WaterTempAverage = -99.9
water_temperature = 0.0
coolingStart_iceCount = 0
coolingStart_waterTemp = 0.0
coolingEnd_waterTemp = 0.0
coolDownDegs = 0.0
coolStartMin = 0
coolEndMin = 0

state = 'idle'

#Initialize weather look parameters
weather_api_key = mySecrets.myWeatherAPI
lat = mySecrets.lat
lon = mySecrets.lon

picodebug.logPrint("Initial Wifi call")
ConnectWifi(1)

picodebug.logPrint("Updating clock")
try:
    if get_worldTime():
        picodebug.logPrint("Clock updated")
except:
    picodebug.logPrint("Failed to update clock")

picodebug.logPrint("Initialize Blynk")
blynk = blynklib.Blynk(BLYNK_AUTH)

@blynk.on("V*")
def read_handler(pin, value):
    picodebug.logPrint("Blynk read handler called")
    global icepacks_added, coolingActive, waterSetpoint, consoleLog

    if pin == '2':
        icepacks_added = value[0]
        #print("Ice packs added: " + value[0])
    if pin == '4':
        coolingActive = value[0]
        #print("Cooling active is " + value[0])
    if pin =='5':
        consoleLog = value[0]
        #print("Conole log: " + value[0])
    if pin == '6':
        waterSetpoint = value[0]
        #print("Water setpoint is " + value[0])


#Main loop ------------------------------------------------
picodebug.logPrint("Entering loop")
while True:
    gc.collect()
    picodebug.logPrint("Get timestamp")
    timestamp = get_uptime()
    
    #Main process ----------------------------------------------
    picodebug.logPrint("Check wifi")
    ConnectWifi(0)

    #ErroLog = timestamp + " test log \n"
    
    #Read Pi W temp sensor value
    picodebug.logPrint("Get temps")
    sensor_temp = machine.ADC(4)
    conversion_factor = 3.3 / (65535)
    reading = sensor_temp.read_u16() * conversion_factor 
    temperature = 27 - (reading - 0.706)/0.001721
    temp_calibrated = temperature - 9.0
    WaterTempSamples.append(temp_calibrated)
    #print(temp_calibrated)

    #Medium loop - Do these actions at a reduced rate compared main loop
    if (CycleLoopCounter % 10) == 0:
        picodebug.logPrint("Entering Medium Loop")
        #Average out 10, 1s samples of water and post that to blynk
        WaterTempAverage = sum(WaterTempSamples) / len(WaterTempSamples)
        water_temperature = WaterTempAverage
        
        #Get new ambient air data from API
        picodebug.logPrint("Get ambient temp")
        try:
            ambient_temperature = get_current_ambient_temperature(weather_api_key, lat, lon)
        except:
            picodebug.logPrint("Get temp failed")         

    if CycleLoopCounter == 100:
        #Look for firmware updates
        picodebug.logPrint("Entering Slow Loop")
        picodebug.logPrint("Checking for firmware updates...")
        picodebug.logPrint("Current version: " + ver)
        ErroLog = "Current version: " + ver
        firmware_url = "github.com/repos/afarzin1/uPython_ColdPlungeTank"
        ota_updater = OTAUpdater("coldPlungeTank",firmware_url, "main.py")
        ota_updater.download_and_install_update_if_available()
        
        CycleLoopCounter = 0
    
    if waterSetpoint != '':
        picodebug.logPrint("Calculate ice packs")
        number_of_ice_packs = calculate_ice_packs(water_temperature, int(waterSetpoint))
    else:
        number_of_ice_packs = 0

    if (coolingActive == '1') and (EventSent_CoolingActive == 0):
        state = 'cooling_started'
        blynk.log_event("cooling_started")
        coolingStart_waterTemp = water_temperature
        coolStartMin = get_uptime_minutes()
        ErroLog = str(timestamp) + " Cooling started at " + str(round(coolingStart_waterTemp,2)) + "deg \n"

        EventSent_CoolingActive = 1
        EventSent_CoolingActive_Off = 0
    
    if state == 'cooling_started' and coolingActive == '0':
        state = 'idle'
        blynk.log_event("cooling_stopped")
        coolingEnd_waterTemp = water_temperature
        coolEndMin = get_uptime_minutes()
        coolTimeMin = coolEndMin - coolStartMin
        #ErroLog = str(timestamp) + " Cooling ended at " + str(round(coolingEnd_waterTemp,2)) + "deg \n"
        coolDownDegs = round(coolingEnd_waterTemp - coolingStart_waterTemp,2)
        ErroLog = str(timestamp) + " Cooled down water by " + str(coolDownDegs) + "deg in " + str(coolTimeMin) + " minutes with " + str(icepacks_added) + " ice packs \n"

        EventSent_CoolingActive = 0
        EventSent_CoolingActive_Off = 1
        
    #Write Values-------------------------------------------------
    picodebug.logPrint("Write Blynk outputs")
    blynk.virtual_write(0, ambient_temperature)
    if not devMode:
        blynk.virtual_write(1, water_temperature)
    blynk.virtual_write(3, number_of_ice_packs)
    blynk.virtual_write(5, ErroLog)
    #blynk.log_event("cooling_started")
    
    picodebug.logPrint("Run Blynk")
    try:
        blynk.run()
    except:
        picodebug.logPrint("Run Blynk failed")

    CycleLoopCounter +=1
    firstScan = 1
    pin.off()
    time.sleep(1)
    ErroLog = ""