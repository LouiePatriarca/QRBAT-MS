import RPi.GPIO as gpio
import time
import picamera2
from smbus2 import SMBus
from mlx90614 import MLX90614


data=""


def capture_image():
    data= time.strftime("%d_%b_%Y|%H:%M:%S")
    camera.start_preview()
    time.sleep(5)
    print(data)
    camera.capture('%s.jpg'%data)
    camera.stop_preview()
    time.sleep(1)

camera = picamera2.picamera2.Picamera2()
camera.rotation=0
camera.awb_mode= 'auto'
camera.brightness=55

while 1:
    bus = SMBus(1)
    sensor = MLX90614(bus, address=0x5A)
    print("Ambient Temperature :", sensor.get_ambient())
    print("Object Temperature :", sensor.get_object_1())
    temp = sensor.get_object_1()
    bus.close()
    if temp>34:
        capture_image()
        time.sleep(0.1)
    else:
        time.sleep(0.01)