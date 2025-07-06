from connections.mqtt import MQTTClient
import keys
import json

def connect_mqtt():
    client = MQTTClient(keys.CLIENT_ID, keys.MQTT_BROKER, port=keys.MQTT_PORT, user=keys.MQTT_USER, password=keys.MQTT_PASS)
    client.connect()
    print("Connected to MQTT broker")
    return client

def mqtt_send(moist, temp, water_level, counter = None, client = None):
    data = {
    "moisture": moist,
    "temperature": temp,
    "water_level": water_level,
    }

    if counter != None:
        data["pump_counter"] = counter

    # Convert to JSON string
    payload = json.dumps(data)
            
    # Publish
    client.publish(keys.MQTT_TOPIC, payload)
    print("Published:", payload)

