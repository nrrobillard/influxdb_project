# InfluxDB Configuration
# Import secrets from secrets.py
try:
    from secrets import INFLUX_TOKEN, OPEN_WEATHER_MAP_TOKEN
except ImportError:
    raise ImportError("secrets.py not found. Copy secrets.py.template to secrets.py and fill in your values.")

bucket = "nickTest"
org = "ORG_NAME"  # or email you used to create your Free Tier Influx
url = "http://influxdb2:8086"  # for Docker setup
# url = "http://localhost:8086"  # for local setup