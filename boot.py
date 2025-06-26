# boot.py -- run on boot-up
import keys
import connections.wifiConnection as wifiConnection 
from connections.mqtt import MQTTClient

client = None
    # Try WiFi Connection
try:
    ip = wifiConnection.connect()
    client = MQTTClient(keys.CLIENT_ID, keys.MQTT_BROKER, user=keys.MQTT_USER, password=keys.MQTT_PASS)
    client.connect()
    print("Connected to MQTT broker")
except Exception as e:
    print("Boot failed:", e)
