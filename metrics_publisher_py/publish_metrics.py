import os
import time
import psutil
from influxdb_client import InfluxDBClient, Point, WriteOptions

INFLUX_URL = os.environ.get("INFLUX_URL", "http://influxdb2:8086")
INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN", "")
INFLUX_ORG = os.environ.get("INFLUX_ORG", "ORG_NAME")
INFLUX_BUCKET = os.environ.get("INFLUX_BUCKET", "nickTest")
INTERVAL = int(os.environ.get("INTERVAL", "10"))

if not INFLUX_TOKEN:
    raise SystemExit("INFLUX_TOKEN environment variable must be set")

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=WriteOptions(batch_size=1))

def gather_metrics():
    cpu_percents = psutil.cpu_percent(interval=None, percpu=True)
    cpu_total = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    points = []
    # CPU per-cpu
    for idx, pct in enumerate(cpu_percents):
        p = Point("cpu")
        p.tag("cpu", str(idx))
        p.field("usage_percent", float(pct))
        points.append(p)

    # CPU total
    p_total = Point("cpu_total").field("usage_percent", float(cpu_total))
    points.append(p_total)

    # Memory
    p_mem = Point("memory").field("total", int(mem.total)).field("available", int(mem.available)).field("used", int(mem.used)).field("used_percent", float(mem.percent))
    points.append(p_mem)

    # Disk
    p_disk = Point("disk").field("total", int(disk.total)).field("used", int(disk.used)).field("free", int(disk.free)).field("used_percent", float(disk.percent))
    points.append(p_disk)

    return points


def main():
    while True:
        try:
            points = gather_metrics()
            for p in points:
                write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=p)
        except Exception as e:
            print("Error writing metrics:", e)
        time.sleep(INTERVAL)

if __name__ == '__main__':
    main()
