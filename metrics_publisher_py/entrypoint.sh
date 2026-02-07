#!/bin/sh
set -e
TOKEN=""
CONFIG_PATH=/config/influx_config.py
if [ -f "$CONFIG_PATH" ]; then
  TOKEN=$(awk -F\" '/INFLUX_TOKEN/ {print $2; exit}' "$CONFIG_PATH")
fi
if [ -z "$TOKEN" ]; then
  echo "INFLUX token not found in $CONFIG_PATH; ensure file exists and defines INFLUX_TOKEN"
  exit 1
fi
export INFLUX_TOKEN="$TOKEN"
exec "$@"
