import network, ntptime, time, machine, mySecrets

def ConnectWifi(printIP):
    
    if not wlan.isconnected():
        while not wlan.isconnected():
            print("Trying to connect...")
            wlan.connect(ssid, password)
            time.sleep(5)
    if wlan.isconnected():
            
        status = wlan.ifconfig()
        if printIP:
            print("Connected to Wifi")
            print( 'ip = ' + status[0] )

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
ssid = mySecrets.mySSID
password = mySecrets.myWifiPassword

ConnectWifi(1)

ntptime.host = 'pool.ntp.org'
ntptime.settime()

# Initialize RTC
rtc = machine.RTC()

# Get the updated time
current_time = time.localtime()

# Set the RTC time
rtc.datetime((current_time[0], current_time[1], current_time[2], current_time[6], current_time[3], current_time[4], current_time[5], 0))

# Verify RTC time
print("RTC time:", rtc.datetime())