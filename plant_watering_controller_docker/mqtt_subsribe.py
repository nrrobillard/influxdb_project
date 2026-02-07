import paho.mqtt.client as mqtt

# Import secrets
try:
    from secrets import MQTT_USERNAME, MQTT_PASSWORD, MQTT_BROKER_IP
except ImportError:
    raise ImportError("secrets.py not found. Copy secrets.py.template to secrets.py and fill in your values.")

# mqtt info
mqtt_username = MQTT_USERNAME
mqtt_password = MQTT_PASSWORD
mqtt_topics = ["raw_moisture_sensor/#", "pulse_water_pump/#"]
mqtt_broker_ip = MQTT_BROKER_IP


# set up mqtt client
client = mqtt.Client()
# Set the username and password for the MQTT client
client.username_pw_set(mqtt_username, mqtt_password)


# These functions handle what happens when the MQTT client connects
# to the broker, and what happens then the topic receives a message
def on_connect(client, userdata, flags, rc):
    # rc is the error code returned when connecting to the broker
    print("Connected!", str(rc))

    # Once the client has connected to the broker, subscribe to the topic
    for topic in mqtt_topics:
        print(f'Subsribing to {topic}')
        client.subscribe(topic)

    
def on_message(client, userdata, msg):
    # This function is called everytime the topic is published to.
    # If you want to check each message, and do something depending on
    # the content, the code to do this should be run in this function
    try:
        print(f'Topic: {msg.topic}')
        print(f'Payload: {msg.payload.decode("utf-8")}')
    except ValueError as e:
        print(f'Error details: {e}')




# Here, we are telling the client which functions are to be run
# on connecting, and on receiving a message
client.on_connect = on_connect
client.on_message = on_message

# Once everything has been set up, we can (finally) connect to the broker
# 1883 is the listener port that the MQTT broker is using
client.connect(mqtt_broker_ip, 1883)

# Once we have told the client to connect, let the client object run itself
client.loop_forever()
client.disconnect()