from ota import OTAUpdater
import network, mySecrets, time
#time.sleep(5)

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


#Look for firmware updates
firmware_url = "github.com/repos/afarzin1/uPython_ColdPlungeTank"
ota_updater = OTAUpdater("coldPlungeTank",firmware_url, "main.py")
ota_updater.download_and_install_update_if_available()