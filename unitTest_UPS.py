import UPS
import time    

# Create an ADS1115 ADC (16-bit) instance.
UPS = UPS.INA219(addr=0x43)
while True:
    bus_voltage = UPS.getBusVoltage_V()             # voltage on V- (load side)
    current = UPS.getCurrent_mA()                   # current in mA
    P = (bus_voltage -3)/1.2*100
    if(P<0):P=0
    elif(P>100):P=100

    # UPS measure bus voltage on the load side. So PSU voltage = bus_voltage + shunt_voltage
    print("Voltage:  {:6.3f} V".format(bus_voltage))
    print("Current:  {:6.3f} A".format(current/1000))
    print("Percent:  {:6.1f} %".format(P))
    print("")
    
    time.sleep(2)