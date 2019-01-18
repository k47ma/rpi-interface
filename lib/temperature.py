import psutil
import time

while True:
    temperatures = psutil.sensors_temperatures()
    for t in sorted(temperatures['coretemp'], key=lambda x: x.label):
        print "{}: {}/{}".format(t.label, t.current, t.critical)
    time.sleep(1)
