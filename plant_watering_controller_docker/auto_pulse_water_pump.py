import paho.mqtt.client as mqtt
import yaml
from datetime import datetime, timedelta
import os
import sys

# Import secrets
try:
    from secrets import MQTT_USERNAME, MQTT_PASSWORD, MQTT_BROKER_IP
except ImportError:
    raise ImportError("secrets.py not found. Copy secrets.py.template to secrets.py and fill in your values.")

# MQTT broker details
port = 1883            
mqtt_username = MQTT_USERNAME
mqtt_password = MQTT_PASSWORD
mqtt_topic = "test"
mqtt_broker_ip = MQTT_BROKER_IP
pulse_water_pump_topic_prefix = "pulse_water_pump/"
raw_moisture_topic_prefix = "raw_moisture_sensor/"

plant_names = ["plant1", "plant2", "plant3", "plant4"]
MAX_RAW_MOISTURE_READING = 500
PULSE_TIME_MS = 3000
WATERING_HISTORY_YAML_PATH = "last_plant_watering_times.yaml"
MAX_HOURS_BETWEEN_WATERING = 120
MIN_HOURS_BETWEEN_WATERING = 24

def pulse_water(pulse_time, plant_name):
    print(f'Watering {plant_name} for {pulse_time} milliseconds')
    message = str(pulse_time)
    topic = pulse_water_pump_topic_prefix + plant_name
    result = client.publish(topic, message)

    # Check if the message was successfully published
    status = result[0]
    if status == 0:
        print(f"Message sent successfully to topic '{topic}'")
    else:
        print(f"Failed to send message to topic '{topic}'")

def load_last_watered_times(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r") as file:
        return yaml.safe_load(file)

def save_last_watered_times(file_path, watered_times):
    with open(file_path, "w") as file:
        yaml.safe_dump(watered_times, file)

def check_and_water_plants(plant, raw_moisture_reading, file_path):
    last_watered_times = load_last_watered_times(file_path)
    now = datetime.now()
    last_watered = last_watered_times.get(plant)
    if last_watered == None:
        print(f'No watering history for {plant} detected. Watering now!')
        pulse_water(PULSE_TIME_MS, plant)
        last_watered_times[plant] = now.isoformat()
    else:
        time_since_last_water = now - datetime.fromisoformat(last_watered)
        print(f'Time since last water: {time_since_last_water}')
        if raw_moisture_reading > MAX_RAW_MOISTURE_READING: # plant moisture sensor indicates we are getting dry
            print('Plant moisture is looking low...')
            if time_since_last_water > timedelta(hours=MIN_HOURS_BETWEEN_WATERING):
                pulse_water(PULSE_TIME_MS, plant)
                last_watered_times[plant] = now.isoformat()
            else:
                hours_left = MIN_HOURS_BETWEEN_WATERING - (time_since_last_water).total_seconds() // 3600
                print(f"{plant} doesn't need water yet. Wait for another {hours_left:.1f} hours.")
        else: # plant moisture sensor indicates it's still wet, but we still want to water if enough time has passed
            if time_since_last_water > timedelta(hours=MAX_HOURS_BETWEEN_WATERING):
                print(f'It has been > {MAX_HOURS_BETWEEN_WATERING} hrs since last water. Watering now.')
                pulse_water(PULSE_TIME_MS, plant)
                last_watered_times[plant] = now.isoformat()

    save_last_watered_times(file_path, last_watered_times)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker!")
    else:
        print(f"Failed to connect, return code {rc}")
    for plant_name in plant_names:
        topic = raw_moisture_topic_prefix + plant_name
        print(f'Subscribing to {topic}')
        client.subscribe(topic)


def on_message(client, userdata, msg):
    # This function is called everytime the topic is published to.
    # If you want to check each message, and do something depending on
    # the content, the code to do this should be run in this function
    print('received message')
    try:
        topic_parts = msg.topic.split('/')  # Split the topic into its components
        if len(topic_parts) == 2:
            sensor_type = topic_parts[0]
            sensor_name = topic_parts[1]
            if sensor_type == 'raw_moisture_sensor':
                raw_moisture_reading = int(msg.payload.decode('utf-8'))
                print(f'Raw moisture reading for {sensor_name}: {raw_moisture_reading}')
                check_and_water_plants(sensor_name, raw_moisture_reading, WATERING_HISTORY_YAML_PATH)
        else:
            print(f"Unexpected topic format: {msg.topic}")

    except ValueError as e:
        print(f'Error details: {e}')



# Create an MQTT client instance
client = mqtt.Client()
client.username_pw_set(mqtt_username, mqtt_password)

# Assign callback for connection
client.on_connect = on_connect

# Assign callback for receiving a message
client.on_message = on_message

# Connect to the MQTT broker
print("Connecting to broker...")
client.connect(mqtt_broker_ip, port, 60)


# client.loop_start()  # Start the loop


client.loop_forever()
client.disconnect()


