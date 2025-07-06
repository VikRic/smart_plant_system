import time                     # Allows use of time.sleep() for delays
import json                     # Interfaces with hardware components
import keys                     # Contain all keys used here
import connections.wifiConnection as wifiConnection           # Contains functions to connect/disconnect from WiFi 
from LCD.I2C_LCD import I2CLcd  # LCD Library
import sensorReads              # All sensor reads & pump activators
import gc                       # Garbage collector
import urequests                # Sending http requests
 
# -------------------- CONSTANTS / GLOBALS --------------------
client = None

LCD_INTERVAL = 30 * 1000             # 30 second interval to update screen
SEND_INTERVAL = 1 * 60 * 60 * 1000   # 1 hour interval to send less frequent updates
PUMP_INTERVAL = 12 * 60 * 60 * 1000  # 12 hour timer in case moisture sensor gives faulty readings.

last_lcd_time = time.ticks_ms() - LCD_INTERVAL
last_sent_time = time.ticks_ms() - SEND_INTERVAL  # So it is ready at start.
last_pump_time = time.ticks_ms() - PUMP_INTERVAL  # So it is ready to pump right away

# Sends water level to discord.
def send_discord_message(msg):
    payload = {"content": "Time to fill up! Waterlevel is at: %d%%" %msg}
    request = urequests.post(keys.DISCORD_URL, data = json.dumps(payload),
    headers = {'Content-Type': 'application/json'})
    request.close()

try: 
    # Set Welcome message
    if sensorReads.devices != []:
        lcd = I2CLcd(sensorReads.lcdScreen, sensorReads.devices[0], 2, 16)
        lcd.move_to(4, 0)
        lcd.putstr("Welcome!")

    # Check connection before MQTT connect
    if not wifiConnection.is_connected():
        wifiConnection.connect()
    else:
        print("WiFi already connected")

    # Get your MQTT client
    from connections.mqttConnection import connect_mqtt, mqtt_send
       
    while True:              # Repeat this loop forever
        time.sleep_ms(1000)
        current_time = time.ticks_ms()

        wifi_connected = wifiConnection.is_connected()
        if not wifi_connected:
            print("Lost wifi, reconnecting...")
            time.sleep(10)
            wifiConnection.connect()
            gc.collect()     

        if wifi_connected and client is None:
            print("Internet OK and no MQTT client - connecting to MQTT...")
            gc.collect()
            client = connect_mqtt()

        if time.ticks_diff(current_time, last_lcd_time) > LCD_INTERVAL:
            print("Internet status:", "OK" if wifi_connected else "NOT available")
            print("Client status:", "OK" if client else "No Client")
            moisture, temperature, water_level = sensorReads.readSensors()
            sensorReads.update_lcd(moisture, water_level)
            last_lcd_time = current_time

        if wifi_connected and time.ticks_diff(current_time, last_sent_time) > SEND_INTERVAL:
            # Publish
            mqtt_send(moisture, temperature, water_level, client = client)
            last_sent_time = current_time
            if water_level < 30:
                send_discord_message(water_level)

        if wifi_connected:
            last_pump_time, pump_data = sensorReads.water_plant(moisture, water_level, last_pump_time, PUMP_INTERVAL)
            if pump_data and client:
                # Publish
                mqtt_send(moisture, temperature, water_level, counter=pump_data["pump_counter"], client = client) 

finally:
    if client is not None:
        client.disconnect()
    wifiConnection.disconnect()
    print("Disconnected")