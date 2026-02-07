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
# replace placeholder in template and write final config
sed "s/__INFLUX_TOKEN__/${TOKEN}/g" /etc/telegraf/telegraf.conf.template > /etc/telegraf/telegraf.conf
exec telegraf -config /etc/telegraf/telegraf.conf
