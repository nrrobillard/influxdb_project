#!/bin/sh
set -e
TOKEN=""
ENV_PATH=/config/.env.local
if [ -f "$ENV_PATH" ]; then
  TOKEN=$(grep '^INFLUX_TOKEN=' "$ENV_PATH" | cut -d'=' -f2)
fi
if [ -z "$TOKEN" ]; then
  echo "INFLUX_TOKEN not found in $ENV_PATH; ensure file exists and defines INFLUX_TOKEN"
  exit 1
fi
# replace placeholder in template and write final config
sed "s/__INFLUX_TOKEN__/${TOKEN}/g" /etc/telegraf/telegraf.conf.template > /etc/telegraf/telegraf.conf
exec telegraf -config /etc/telegraf/telegraf.conf
