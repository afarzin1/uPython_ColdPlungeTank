import machine

def GetTimestamp():
    rawTime = machine.RTC().datetime()
    print(rawTime)
    timeStamp = str(rawTime[0]) + '-' + str(rawTime[1]) + '-' + str(rawTime[2]) + ' ' + str(rawTime[4]) + ':' + str(rawTime[5]) + ':' + str(rawTime[6])
    return timeStamp

print(GetTimestamp())