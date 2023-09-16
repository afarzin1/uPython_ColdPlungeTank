import ntptime, network, mySecrets, machine, time

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
def ConnectWifi(printIP):

    attemptCounter = 0
    
    if not wlan.isconnected():
        while not wlan.isconnected():
            if attemptCounter == 5:
                #picodebug.logPrint("Wifi not connecting, rebooting...",OutputToConsole,OutputToFile)
                machine.reset()
            print("Trying to connect...")
            wlan.connect(ssid, password)
            #pin.toggle()
            attemptCounter += 1
            time.sleep(3)
    if wlan.isconnected():
            
        status = wlan.ifconfig()
        if printIP:
            print("Connected to Wifi")
            print( 'ip = ' + status[0] )

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

def GetTimestamp():
    rawTime = machine.RTC().datetime()
    print(rawTime)
    timeStamp = str(rawTime[0]) + '-' + str(rawTime[1]) + '-' + str(rawTime[2]) + ' ' + str(rawTime[4]) + ':' + str(rawTime[5]) + ':' + str(rawTime[6])
    return timeStamp

def IsItPrimTime(startHour, EndHour):
    rawTime = machine.RTC().datetime()
    hour = rawTime[4]
    if (hour >= startHour) and (hour < EndHour):
        return 1
    else:
        return 0

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
ssid = mySecrets.mySSID
password = mySecrets.myWifiPassword

ConnectWifi(1)
get_worldTime()
mytime = GetTimestamp()
rawTime = machine.RTC().datetime()
hour = rawTime[4]

print(GetTimestamp())

print(IsItPrimTime(18,19))
