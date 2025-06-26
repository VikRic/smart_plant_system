from connections.mqtt import MQTTClient
import keys

def connect_mqtt():
    client = MQTTClient(keys.CLIENT_ID, keys.MQTT_BROKER, port=keys.MQTT_PORT, user=keys.MQTT_USER, password=keys.MQTT_PASS)
    client.connect()
    print("Connected to MQTT broker")
    return client
