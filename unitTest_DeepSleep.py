import machine
import time

pin = machine.Pin("LED", machine.Pin.OUT)
counter = 0

while counter<10:
    pin.toggle()
    time.sleep(0.5)
    counter +=1

    if counter == 5:
        machine.deepsleep(5000)

    if counter == 9:
        counter = 0
