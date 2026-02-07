# MQTT Configuration
# Import secrets from secrets.py
try:
    from secrets import MQTT_USERNAME, MQTT_PASSWORD, MQTT_BROKER_IP
except ImportError:
    raise ImportError("secrets.py not found. Copy secrets.py.template to secrets.py and fill in your values.")

mqtt_username = MQTT_USERNAME
mqtt_password = MQTT_PASSWORD
mqtt_broker_ip = MQTT_BROKER_IP