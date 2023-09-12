from machine import RTC
from time import sleep


def logPrint(myParam, outputToConsole = True, outputToFile = True, makeTimeStamp = True, led = None, numberOfBlinks = 0):
    
    if outputToConsole:
        print(f"{RTC().datetime()} - {myParam}")
    if outputToFile:
        with open("log1.txt", "ab") as f:
            if makeTimeStamp:
                f.write(f"{RTC().datetime()} - {myParam}\n")
            else:
                f.write(f"{myParam}\n")
    if numberOfBlinks > 0:
        count = 0
        while count < numberOfBlinks:
            count = count + 1
            led.on()
            sleep(0.3)
            led.off()
            sleep(0.1)
        

def logClean():
    import os

    # List all files in the current directory
    all_files = os.listdir()

    # Filter files that start with 'log' and end with '.txt'
    log_files = [f for f in all_files if f.startswith('log') and f.endswith('.txt')]

    for filename in log_files:
        try:
            # Check if the file exists
            os.stat(filename)
            # If the above line doesn't raise an exception, the file exists and can be removed
            os.remove(filename)
        except OSError:
            # File doesn't exist or couldn't be removed
            pass

def logRotate():
    import os

    fileSize = 0
    maxSize = 50000
    maxFiles = 3

    try:
        fileSize = os.stat('log1.txt')[6]

        #We should do rotation
        if fileSize >= maxSize:
    
            #Remove last file and free space 
            try:
     
                os.remove(f"log{maxFiles}.txt")
               
            except:
              
                pass

            #Shift files 
            for i in range(maxFiles - 1, 0, -1):
           
                try:
         
                    os.rename(f"log{i}.txt", f"log{i+1}.txt")
             
                except:
                 
                    pass
    except:
        pass