from machine import Pin, PWM, I2C
import time
from soil_sensor.stemma_soil_sensor import StemmaSoilSensor
from LCD.I2C_LCD import I2CLcd


# Setup pins and sensors

# UltraSonic Range pins
Trig = Pin(19, Pin.OUT, 0)
Echo = Pin(18, Pin.IN, 0)
soundVelocity = 340

# Pump pins
pumpPin1 = Pin(16, Pin.OUT)
pumpPin2 = Pin(13, Pin.OUT)
enable = Pin(17, Pin.OUT)
enable.value(0)  # Set it to off to lower power consumption.


lcdScreen = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)
devices = lcdScreen.scan()
lcd = None
if devices:
    lcd = I2CLcd(lcdScreen, devices[0], 2, 16)

sensor = I2C(sda=Pin(0), scl=Pin(1), freq=400000)
seesaw = StemmaSoilSensor(sensor)

PUMP_COUNTER = 0 # To see how many times the pump has been activated.
PUMP_DURATION = 10 # How long the pump should be active
MOISTURE_THRESHOLD = 400 # Threshold before watering plant starts
LCD_INTERVAL = 30 * 1000 # 30 second interval
SEND_INTERVAL = 1 * 60 * 60 * 1000  # Timer to send less frequent updates
PUMP_INTERVAL = 12 * 60 * 60 * 1000  # Timer incase moisture sensor gives faulty readings.
last_pump_time = time.ticks_ms() - PUMP_INTERVAL  # So it is ready to pump right away
current_time = time.ticks_ms()

# -------------------- Sensor Utility --------------------
# Get distance from Ultrasonic ranging device
def getDistance():
    Trig.value(1)
    time.sleep_us(10)
    Trig.value(0)
    
    timeout = 100000  # microseconds
    count = 0
    while not Echo.value():
        count += 1
        if count > timeout:
            print("Timeout waiting for Echo HIGH")
            return -1

    pingStart = time.ticks_us()
    count = 0
    while Echo.value():
        count += 1
        if count > timeout:
            print("Timeout waiting for Echo LOW")
            return -1

    pingStop = time.ticks_us()
    distanceTime = time.ticks_diff(pingStop, pingStart) // 2
    distance = int(soundVelocity * distanceTime // 10000)

    return distance

# For more accurate reading of sensors
def getAverage(avgValue, samples = 10):
    results = []
    for i in range(samples):
        value = avgValue()
        if value != -1: # Error code
            results.append(value)
        time.sleep(0.05) # Delay on each loop helps stabilize reads.
    if results:
        return sum(results) / len(results)
    return -1

# Get waterLevel of reservoir. Max & Min level are cm of reservoir
def waterLevel(maxLevel = 20, minLevel = 37):
    distance = getAverage(getDistance)
    water_level = (minLevel - distance) / (minLevel - maxLevel) * 100
    return int(water_level)

# Get all sensor data
def readSensors():
    moisture = getAverage(seesaw.get_moisture)
    temperature = getAverage(seesaw.get_temp)
    water_level = waterLevel() 

    print("Water Level: ", water_level,"%")
    print("MOIST: ", moisture)
    print("TEMP: ", temperature)
    return moisture, temperature, water_level


# Update LCD Screen
def update_lcd(moisture, water_level):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("Moisture: %d" % moisture)
    lcd.move_to(0, 1)
    lcd.putstr("Water Level:%d" % water_level)

# -------------------- PUMP CONTROL --------------------
def pump_on(water_level):
    global PUMP_COUNTER
    print("Activating pump")
    enable.value(1)
    pumpPin1.value(1)
    pumpPin2.value(0)
    PUMP_COUNTER += 1

    data = {
        "pump_counter": PUMP_COUNTER,
        "water_level": water_level
    }
    return data

def pump_off():
    pumpPin1.value(0)
    pumpPin2.value(0)
    enable.value(0)

def water_plant(moisture, waterlevel, last_pump_time, PUMP_INTERVAL):
        # Automatically pumps water
    if moisture < MOISTURE_THRESHOLD and waterlevel > 20 and time.ticks_diff(time.ticks_ms(), last_pump_time) > PUMP_INTERVAL:
        print("Watering plant...")
        pump_data = pump_on(waterLevel)
        time.sleep(PUMP_DURATION)
        pump_off()
        print("Pump deactivated")
        return time.ticks_ms(), pump_data
    else:
        pump_off()
        return last_pump_time, None
    