import machine, time

sensor = machine.ADC(0)
conversion_factor = 3.3 / (65535)

def scale_value(value, input_min=0, input_max=1.75, output_min=0, output_max=100):
    scaled_value = ((value - input_min) / (input_max - input_min)) * (output_max - output_min) + output_min
    return scaled_value


while True:
    reading = sensor.read_u16() * conversion_factor 
    print(scale_value(reading))
    time.sleep(0.5)