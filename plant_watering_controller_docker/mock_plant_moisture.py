import paho.mqtt.client as mqtt
import click
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
pulse_water_pump_topic_prefix = "raw_moisture_sensor/"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker!")
    else:
        print(f"Failed to connect, return code {rc}")

@click.command()
@click.option("--moisture", default="200", help="Mock moisture to send.")
@click.option("--name", default="plant_mock", help="Name of Mock plant")
def main(moisture, name):
    # Create an MQTT client instance
    client = mqtt.Client()
    client.username_pw_set(mqtt_username, mqtt_password)

    # Assign callback for connection
    client.on_connect = on_connect

    # Connect to the MQTT broker
    print("Connecting to broker...")
    client.connect(mqtt_broker_ip, port, 60)

    client.loop_start()  # Start the loop

    # Publish a message to the topic
    message = moisture
    pulse_water_pump_topic = pulse_water_pump_topic_prefix + name
    result = client.publish(pulse_water_pump_topic, message)

    # Check if the message was successfully published
    status = result[0]
    if status == 0:
        print(f"Message sent successfully to topic '{pulse_water_pump_topic}'")
    else:
        print(f"Failed to send message to topic '{pulse_water_pump_topic}'")

    client.loop_stop()  # Stop the loop
    client.disconnect()  # Disconnect from the broker

if __name__ == "__main__":
    main()