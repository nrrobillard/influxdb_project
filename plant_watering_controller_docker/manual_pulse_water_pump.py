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
pulse_water_pump_topic_prefix = "pulse_water_pump/"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker!")
    else:
        print(f"Failed to connect, return code {rc}")


@click.command()
@click.option("--plant", help="Plant to water.")
@click.option("--seconds", default=1, help="Number of seconds for pulse.")
def main(plant, seconds):
    # Create an MQTT client instance
    client = mqtt.Client()
    client.username_pw_set(mqtt_username, mqtt_password)

    # Assign callback for connection
    client.on_connect = on_connect

    # Connect to the MQTT broker
    print("Connecting to broker...")
    client.connect(mqtt_broker_ip, port, 60)

    # Publish a message to the topic
    message = str(1000*seconds)
    client.loop_start()  # Start the loop
    topic = pulse_water_pump_topic_prefix + plant
    result = client.publish(topic, message)

    # Check if the message was successfully published
    status = result[0]
    if status == 0:
        print(f"Message sent successfully to topic '{topic}'")
    else:
        print(f"Failed to send message to topic '{topic}'")

    client.loop_stop()  # Stop the loop
    client.disconnect()  # Disconnect from the broker



if __name__ == "__main__":
    main()
