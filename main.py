import time, picodebug, mySecrets
import machine

time.sleep(5)

ver="1.56"
devMode = False
hasUPS = True
OutputToConsole = False
OutputToFile = False

#picodebug.logClean()
picodebug.logPrint("Initializing",OutputToConsole,OutputToFile)

#turn on LED for first-scan
pin = machine.Pin("LED", machine.Pin.OUT)
pin.on()

picodebug.logPrint("Importing libs",OutputToConsole,OutputToFile)
import network,time,urequests,json, ntptime, os
from ota import OTAUpdater
import math
import machine
import blynklib
import gc
import UPS

#First scan initialization
firstScan = 0
CycleLoopCounter = 0

if devMode:
    BLYNK_AUTH = mySecrets.blynkauth_dev
else:    
    BLYNK_AUTH = mySecrets.blynkauth

#Init Tags--------------------------------------------------
icepacks_added = ""
coolingActive = ""
waterSetpoint = ""
consoleLog = ""
ambient_temperature = ""
remoteTerminal = ""
EventSent_CoolingActive = 0
EventSent_CoolingActive_Off = 0
WaterTempSamples = []
WaterTempAverage = -99.9
water_temperature = -99.0
coolingStart_iceCount = 0
coolingStart_waterTemp = 0.0
coolingEnd_waterTemp = 0.0
coolDownDegs = 0.0
coolStartMin = 0
coolEndMin = 0
batterySoC = 0
cmdPing = False
cmdVer = False
cmdUpdate = False
cmdReset = False
cmdSoft_Rest = False
cmdPeakHours_ON = False
cmdPeakHours_OFF = False
cmdPeakHours_Auto = True
peakHours = True
peakHours_Start = 6
peakHours_End = 11

state = 'idle'

#Initialize weather look parameters
weather_api_key = mySecrets.myWeatherAPI
lat = mySecrets.lat
lon = mySecrets.lon

#Initialize OTA
firmware_url = "github.com/repos/afarzin1/uPython_ColdPlungeTank"
ota_updater = OTAUpdater("coldPlungeTank",firmware_url, "main.py")

#Init WIFI
picodebug.logPrint("Initializing WIFI",OutputToConsole,OutputToFile)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
ssid = mySecrets.mySSID
password = mySecrets.myWifiPassword

#Init UPS
# Create an ADS1115 ADC (16-bit) instance.
if hasUPS:
    UPS = UPS.INA219(addr=0x43)

def ConnectWifi(printIP):

    attemptCounter = 0
    
    if not wlan.isconnected():
        while not wlan.isconnected():
            if attemptCounter == 5:
                picodebug.logPrint("Wifi not connecting, rebooting...",OutputToConsole,OutputToFile)
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

def GetTimestamp():
    rawTime = machine.RTC().datetime()
    print(rawTime)
    timeStamp = str(rawTime[0]) + '-' + str(rawTime[1]) + '-' + str(rawTime[2]) + ' ' + str(rawTime[4]) + ':' + str(rawTime[5]) + ':' + str(rawTime[6])
    return timeStamp

def GetFreeSpace():
    # Get the status of the file system
    stat = os.statvfs('/')

    # Calculate the available space
    block_size = stat[0]  # Size of a block
    total_blocks = stat[2]  # Total data blocks in the file system
    free_blocks = stat[3]  # Free blocks in the file system

    # Calculate total and free space in bytes
    total_space = block_size * total_blocks
    free_space = block_size * free_blocks

    return free_space

def get_current_ambient_temperature(api_key, lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = urequests.get(url)
    #time.sleep(2)
    if response.status_code == 200:
        data = json.loads(response.text)
        current_temperature = data['main']['feels_like']
        data = ""
        response = ""
        return current_temperature
    else:
        return f"Error: {response.status_code}"

def calculate_ice_packs(T_initial, T_final):
    m_water = 184955  # mass of 48.85 gallons of water in grams
    c = 7.18  # specific heat capacity of water in J/g°C
    Lf = 300  # heat of fusion for water in J/g
    m_ice_pack = 2600  # mass of one ice pack in grams

    E_needed = m_water * c * (T_initial - T_final)
    E_ice_pack = m_ice_pack * (Lf + c * T_final)

    N = E_needed / E_ice_pack
    N = math.ceil(N)  # Round up to the nearest whole number
    return N

def GetBatSoc():
    global hasUPS
    if hasUPS:
        bus_voltage = UPS.getBusVoltage_V()             # voltage on V- (load side)
        current = UPS.getCurrent_mA()                   # current in mA
        P = (bus_voltage -3)/1.2*100
        if(P<0):P=0
        elif(P>100):P=100
        return P
    else:
        return 1.11

def PeakHoursNow(startHour, EndHour):
    rawTime = machine.RTC().datetime()
    hour = rawTime[4]
    if (hour >= startHour) and (hour < EndHour):
        return 1
    else:
        return 0

#Connect to Wifi
picodebug.logPrint("Initial Wifi call",OutputToConsole,OutputToFile)
try:
    ConnectWifi(1)
except:
    machine.reset()

#Update RTC to actual time
picodebug.logPrint("Updating clock",OutputToConsole,OutputToFile)
try:
    if get_worldTime():
        picodebug.logPrint("Clock updated",OutputToConsole,OutputToFile)
except:
    picodebug.logPrint("Failed to update clock",OutputToConsole,OutputToFile)
    machine.reset()


#Get Battery SoC
batterySoC = GetBatSoc()

FreeMem = gc.mem_free() / 1000
FreeSpace = GetFreeSpace() / 1000

remoteTerminal = GetTimestamp() +" Booting up v" + ver + "\n"

#Initialize Blynk
picodebug.logPrint("Initialize Blynk",OutputToConsole,OutputToFile)
blynk = blynklib.Blynk(BLYNK_AUTH)

@blynk.on("V*")
def read_handler(pin, value):
    picodebug.logPrint("Blynk read handler called",OutputToConsole,OutputToFile)
    global icepacks_added, coolingActive, waterSetpoint, remoteTerminal, FreeMem, FreeSpace, number_of_ice_packs

    if pin == '2':
        icepacks_added = value[0]
        #print("Ice packs added: " + value[0])
    if pin == '3':
        number_of_ice_packs = value[0]
    
    if pin == '4':
        coolingActive = value[0]
        #print("Cooling active is " + value[0])
    if pin =='5':
        remoteTerminal = value[0]
        #print("Conole log: " + value[0])
    if pin == '6':
        waterSetpoint = value[0]
        #print("Water setpoint is " + value[0])

#Read initial values
blynk.run()
time.sleep(0.25)

#Main loop ------------------------------------------------
picodebug.logPrint("Entering loop",OutputToConsole,OutputToFile)
while True:
    try:
        gc.collect()
        picodebug.logPrint("Get timestamp",OutputToConsole,OutputToFile)
        #timestamp = get_uptime()
        
        #Main process ----------------------------------------------
        picodebug.logPrint("Check wifi",OutputToConsole,OutputToFile)
        ConnectWifi(0)
        
        #Read Water Temperature
        picodebug.logPrint("Get temps",OutputToConsole,OutputToFile)
        sensor_temp = machine.ADC(4)
        conversion_factor = 3.3 / (65535)
        reading = sensor_temp.read_u16() * conversion_factor 
        temperature = 27 - (reading - 0.706)/0.001721
        if peakHours:
            temp_calibrated = temperature - 5.6
        else:
            temp_calibrated = temperature - 3.9
        WaterTempSamples.append(temp_calibrated)

        #Check if peak usage hours
        if (PeakHoursNow(peakHours_Start,peakHours_End)):
            picodebug.logPrint("Peak Hours On",OutputToConsole,OutputToFile)
            peakHours = True
        else:
            picodebug.logPrint("Peak Hours Off",OutputToConsole,OutputToFile)
            peakHours = False   
        
        gc.collect()

        #10s Loop
        if (CycleLoopCounter % 10) == 0:
            picodebug.logPrint("Entering 10s Loop",OutputToConsole,OutputToFile)
            
            #Average out 10, 1s samples of water and post that to blynk
            if len(WaterTempSamples) > 9:
                WaterTempAverage = sum(WaterTempSamples) / len(WaterTempSamples)
                water_temperature = WaterTempAverage
                WaterTempSamples.clear()                           
        #30s Loop
        if (CycleLoopCounter % 30 == 0):
            #Get new ambient air data from API
            picodebug.logPrint("Get ambient temp",OutputToConsole,OutputToFile)
            try:
                ambient_temperature = get_current_ambient_temperature(weather_api_key, lat, lon)
            except:
                picodebug.logPrint("Get temp failed")

            #Get Battery SoC
            picodebug.logPrint("Checking battery SoC:",OutputToConsole,OutputToFile)
            batterySoC = GetBatSoc()
        #60s loop
        if (CycleLoopCounter % 60 == 0) and CycleLoopCounter > 0:
            if (not peakHours) and (remoteTerminal != "force_wake"):
                machine.Pin(23, machine.Pin.OUT).low()
                machine.deepsleep(600000)
        
        #900s Loop
        if CycleLoopCounter == 900:
            #Rotate log files
            if OutputToFile:
                picodebug.logPrint("Entering 900s Loop",OutputToConsole,OutputToFile)
                picodebug.logPrint("Rotating logs",OutputToConsole,OutputToFile)
                picodebug.logRotate()   
            
        #Reset due to mystery memory leak
        if CycleLoopCounter == 3600:
            if state != 'cooling_started':
                machine.reset()
            CycleLoopCounter = 0
        
        #Calcualte number of ice packs needed
        if waterSetpoint != '':
            picodebug.logPrint("Calculate ice packs",OutputToConsole,OutputToFile)
            number_of_ice_packs = calculate_ice_packs(water_temperature, int(waterSetpoint))
        else:
            number_of_ice_packs = 0

        gc.collect()

        #Cooling ON State
        if (coolingActive == '1') and (EventSent_CoolingActive == 0):
            state = 'cooling_started'
            blynk.log_event("cooling_started")
            coolingStart_waterTemp = water_temperature
            coolStartMin = get_uptime_minutes()
            remoteTerminal = GetTimestamp() + " Cooling started at " + str(round(coolingStart_waterTemp,2)) + "deg \n"

            EventSent_CoolingActive = 1
            EventSent_CoolingActive_Off = 0
        
        #Cooling OFF State
        if state == 'cooling_started' and coolingActive == '0':
            state = 'idle'
            blynk.log_event("cooling_stopped")
            coolingEnd_waterTemp = water_temperature
            coolEndMin = get_uptime_minutes()
            coolTimeMin = coolEndMin - coolStartMin
            #remoteTerminal = str(timestamp) + " Cooling ended at " + str(round(coolingEnd_waterTemp,2)) + "deg \n"
            coolDownDegs = round(coolingEnd_waterTemp - coolingStart_waterTemp,2)
            remoteTerminal = GetTimestamp() + " Cooled down water by " + str(coolDownDegs) + "deg in " + str(coolTimeMin) + " minutes with " + str(icepacks_added) + " ice packs \n"
            EventSent_CoolingActive = 0
            EventSent_CoolingActive_Off = 1
            
        #Remote Console Command handling-------------------------------------------------
        if cmdPing:
            remoteTerminal = "\n" + str(CycleLoopCounter)
            cmdPing = False
        
        if cmdUpdate:
            picodebug.logPrint("Remote request for firmare update",OutputToConsole,OutputToFile)
            ota_updater.download_and_install_update_if_available()
            cmdUpdate = False
        
        if cmdReset:
            picodebug.logPrint("Remote request for reset",OutputToConsole,OutputToFile)
            machine.reset()
            cmdReset = False
        
        if cmdSoft_Rest:
            picodebug.logPrint("Remote request for soft reset",OutputToConsole,OutputToFile)
            machine.soft_reset()
            cmdSoft_Rest = False
        
        if cmdVer:
            remoteTerminal = "\n" + str(ver)
            cmdVer = False
           
        #Write outputs
        picodebug.logPrint("Write Blynk outputs",OutputToConsole,OutputToFile)
        blynk.virtual_write(0, ambient_temperature)
        if water_temperature != -99.0:
            blynk.virtual_write(1, water_temperature)
        blynk.virtual_write(3, number_of_ice_packs)
        blynk.virtual_write(5, remoteTerminal)
        blynk.virtual_write(7, FreeMem)
        blynk.virtual_write(8, FreeSpace)
        blynk.virtual_write(10, batterySoC)
            
        picodebug.logPrint("Run Blynk",OutputToConsole,OutputToFile)
        
        blynk.run()
        time.sleep(0.25)
        gc.collect()

        #Remote requests
        if remoteTerminal == "update":
            cmdUpdate = True

        if remoteTerminal == "reset":
            cmdReset = True
 
        if remoteTerminal == "soft_reset":
            cmdSoft_Rest = True

        if remoteTerminal == "ping":
            cmdPing = True
        
        if remoteTerminal == "ver":
            cmdVer = True
            
        #Loop end cleanup
        CycleLoopCounter +=1
        firstScan = 1
        pin.off()
        
        #Cleanup loop memory
        if remoteTerminal != "force_wake":
            remoteTerminal = ""
        
        picodebug.logPrint("Free memory: {}".format(FreeMem),OutputToConsole,OutputToFile) 
        picodebug.logPrint("Free space: {}".format(FreeSpace),OutputToConsole,OutputToFile)
        
        time.sleep(1)
    except:
        machine.reset()