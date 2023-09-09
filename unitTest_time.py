import utime

def get_uptime():
    # Get the current uptime in milliseconds
    uptime_ms = utime.ticks_ms()
    
    # Calculate hours, minutes, and seconds
    uptime_s = uptime_ms // 1000
    hours = uptime_s // 3600
    minutes = (uptime_s % 3600) // 60
    seconds = uptime_s % 60
    
    return "{}:{}:{}".format(hours, minutes, seconds)

while True:
    print("Uptime:", get_uptime())
    utime.sleep(1)
