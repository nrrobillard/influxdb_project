# MQTT Configuration
# Import secrets from config_secrets.py
try:
    from config_secrets import MQTT_USERNAME, MQTT_PASSWORD, MQTT_BROKER_IP
except ImportError:
    raise ImportError("config_secrets.py not found. Please ensure .env.local is configured.")

mqtt_username = MQTT_USERNAME
mqtt_password = MQTT_PASSWORD
mqtt_broker_ip = MQTT_BROKER_IP