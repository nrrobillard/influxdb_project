# InfluxDB Configuration
# Import secrets from config_secrets.py
import logging
import os
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

logging.info("Loading InfluxDB configuration from config_secrets.py...")
try:
    from config_secrets import INFLUX_TOKEN, OPEN_WEATHER_MAP_TOKEN
except ImportError:
    raise ImportError("config_secrets.py not found. Please ensure .env.local is configured")
bucket = "nickTest"
org = "ORG_NAME"  # or email you used to create your Free Tier Influx
url = "http://influxdb2:8086"  # for Docker setup
# url = "http://localhost:8086"  # for local setup

# logging.info("INFLUX_TOKEN loaded: " + ("Yes" if INFLUX_TOKEN else "No"))
# logging.info("InfluxDB configuration loaded successfully.")