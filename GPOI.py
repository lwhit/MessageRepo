import RPi.GPIO as GPIO
import time

count = 253

# pin 21 = blue, pin 20 = green, pin 16 = red
# White: +All
# Yellow: Red+Green
# Magenta: Red+Blue

GPIO.setmode( GPIO.BCM )
GPIO.setwarnings(False)
GPIO.setup(16, GPIO.OUT)
GPIO.setup(20, GPIO.OUT)
GPIO.setup(21, GPIO.OUT)

a = 0
b = 0
c = 0

a = count % 10
count = (count - a) / 10

b = count % 10
count = (count - b) / 10

c = count

# Red blink
while (c != 0):
    GPIO.output(16, True)
    GPIO.output(20, False)
    GPIO.output(21, False)

    time.sleep(1)
    GPIO.output(16, False)
    time.sleep(1)
    c -= 1

# Blue blink
while (b != 0):
    GPIO.output(21, True)

    time.sleep(1)
    GPIO.output(21, False)
    time.sleep(1)
    b -= 1

# Green blink
while (a != 0):
    GPIO.output(20, True)

    time.sleep(1)
    GPIO.output(20, False)
    time.sleep(1)
    a -= 1

GPIO.cleanup()
