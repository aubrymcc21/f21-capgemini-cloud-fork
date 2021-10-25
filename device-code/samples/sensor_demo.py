from smbus2 import SMBus
from mlx90614 import MLX90614
import picamera

bus = SMBus(1)
sensor = MLX90614(bus, address=0x5A)

print ("Ambient Temperature: ", sensor.get_ambient())
print ("Object Temperature: ", sensor.get_object_1())

bus.close()

from time import sleep

camera = picamera.PiCamera()
camera.start_preview()

sleep(2)

camera.capture("test.jpg")
