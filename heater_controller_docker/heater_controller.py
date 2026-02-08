# import paho.mqtt.client as mqtt

import influxdb_client
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import asyncio
from aiomqtt import Client as AIOMQTT
from kasa import SmartPlug
from aiohttp import web
import pathlib

import influx_config
import mqtt_config
from time import sleep, monotonic
import logging
import os



log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# mqtt info
mqtt_username = mqtt_config.mqtt_username
mqtt_password = mqtt_config.mqtt_password
mqtt_broker_ip = mqtt_config.mqtt_broker_ip

logging.info(f"MQTT Configuration: broker={mqtt_broker_ip}, username={'set' if mqtt_username else 'not set'}")


# influx info
bucket = influx_config.bucket
org =  influx_config.org 
token = influx_config.INFLUX_TOKEN
url = influx_config.url


# sensor option
SENSOR_OPTIONS = [ "living_room", "bedroom", "plants" ]

# heater temperature settings (defaults)
ON_TEMPERATURE_DEGF = 63.0
OFF_TEMPERATURE_DEGF = 68.0

# name of the sensor to use for controlling the heater. This should match the second part of the MQTT topic, e.g. "temperature_degC/plants" would be "plants"
CONTROL_SENSOR_NAME = "living_room"

# mutable control sensor name (can be changed via REST)
control_sensor_name = CONTROL_SENSOR_NAME
control_sensor_lock = asyncio.Lock()

thresholds = {'on': ON_TEMPERATURE_DEGF, 'off': OFF_TEMPERATURE_DEGF}
thresholds_lock = asyncio.Lock()


# heater IP address # TODO: make this figure this out automatically
# heater_ip = '192.168.0.140' # lamp ip for debug
heater_ip = '192.168.0.146'

# set up mqtt client
# logging.info("Setting up MQTT client...")
# client = mqtt.Client()

# Set the username and password for the MQTT client
# client.username_pw_set(mqtt_username, mqtt_password)

# wait 5 seconds to give influxdB time to start up. TODO: make this somehow poll until the influx is ready
logging.info("Waiting 5s InfluxDB to start...")
sleep(5)


# set mqtt topic to subscribe to
temperature_topic = "temperature_degC/#"

# set up influxdB client
write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
write_api = write_client.write_api(write_options=SYNCHRONOUS)


# client.heater_on = False  # Initial state of the heater


def celsius_to_fahrenheit(celsius):
    return round((celsius * 9.0/5.0) + 32.0,2)

# def on_connect(client, userdata, flags, rc):
#     # rc is the error code returned when connecting to the broker
#     logging.info(f"Connected! {str(rc)}")

#     # Once the client has connected to the broker, subscribe to the topic
#     # client.subscribe(mqtt_topic)
#     client.subscribe(temperature_topic)

# def on_message(client, userdata, msg):
#     # This function is called everytime the topic is published to.
#     # If you want to check each message, and do something depending on
#     # the content, the code to do this should be run in this function
#     try:
#         topic_parts = msg.topic.split('/')  # Split the topic into its components
#         if len(topic_parts) == 2:
#             sensor_type = topic_parts[0]
#             sensor_name = topic_parts[1]
#             if sensor_type == 'temperature_degC':
#                 topic_parts = msg.topic.split('/')  # Split the topic into its components
#                 temperature_degF = celsius_to_fahrenheit(float(msg.payload.decode('utf-8')))
#                 logging.info(f'Temperature for {sensor_name}: {temperature_degF}°F')
#                 if sensor_name == 'living_room':   
#                     if temperature_degF < ON_TEMPERATURE_DEGF:
#                         if not client.heater_on:
#                             logging.info("Heater ON")
#                             client.heater_on = True
#                     elif temperature_degF > OFF_TEMPERATURE_DEGF:
#                         if client.heater_on:
#                             logging.info("Heater OFF")
#                             client.heater_on = False
#                     # point = (
#                     #     Point('room_temp')
#                     #     .tag("location", sensor_name)
#                     #     .field(sensor_name + '_temp_degF', temperature_degF)
#                     # )
#                     # write_api.write(bucket=bucket, org=org, record=point)
#         else:
#             logging.warning(f"Unexpected topic format: {msg.topic}")
#     except ValueError as e:
#         logging.error(f'Error details: {e}')


# # Here, we are telling the client which functions are to be run
# # on connecting, and on receiving a message
# client.on_connect = on_connect
# client.on_message = on_message

# # Once everything has been set up, we can (finally) connect to the broker
# # 1883 is the listener port that the MQTT broker is using
# client.connect(mqtt_broker_ip, 1883)

# # Once we have told the client to connect, let the client object run itself
# client.loop_forever()
# client.disconnect()


async def start_rest_server(host='0.0.0.0', port=8000, influx_q=None):
    async def get_thresholds(request):
        async with thresholds_lock:
            return web.json_response({'on': thresholds['on'], 'off': thresholds['off']})

    async def set_thresholds(request):
        data = await request.json()
        async with thresholds_lock:
            if 'on' in data:
                thresholds['on'] = float(data['on'])
            if 'off' in data:
                thresholds['off'] = float(data['off'])
            current = {'on': thresholds['on'], 'off': thresholds['off']}
        return web.json_response(current)

    async def get_control_sensor(request):
        async with control_sensor_lock:
            return web.json_response({'control_sensor': control_sensor_name})

    async def set_control_sensor(request):
        data = await request.json()
        if 'control_sensor' not in data:
            return web.json_response({'error': 'control_sensor required'}, status=400)
        sensor = data['control_sensor']
        if sensor not in SENSOR_OPTIONS:
            return web.json_response({'error': 'invalid sensor'}, status=400)
        async with control_sensor_lock:
            global control_sensor_name
            control_sensor_name = sensor
        # persist choice to InfluxDB so it survives restarts
        if influx_q is not None:
            try:
                point = (
                    Point('controller_config')
                    .tag('location', 'heater')
                    .field('control_sensor', control_sensor_name)
                )
                await influx_q.put(point)
            except Exception:
                logging.exception('failed to enqueue control_sensor to influx')
        else:
            logging.warning('influx_q not provided; control_sensor config not persisted')

        return web.json_response({'control_sensor': control_sensor_name})

    async def get_sensor_options(request):
        return web.json_response({'options': SENSOR_OPTIONS})

    app = web.Application()
    app.add_routes([
        web.get('/thresholds', get_thresholds), web.post('/thresholds', set_thresholds),
        web.get('/control_sensor', get_control_sensor), web.post('/control_sensor', set_control_sensor),
        web.get('/sensor_options', get_sensor_options),
    ])

    # serve static UI from ./web/index.html
    web_dir = pathlib.Path(__file__).resolve().parent / 'web'
    # if you want index at '/', point to index.html
    async def index(request):
        return web.FileResponse(web_dir / 'index.html')

    app.router.add_get('/', index)
    app.router.add_static('/static/', path=str(web_dir), show_index=False)


    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logging.info(f"REST server running on http://{host}:{port}")
    return runner


async def load_control_sensor_from_influx():
    try:
        query_api = write_client.query_api()
        flux = f'from(bucket:"{bucket}") |> range(start: 0) |> filter(fn: (r) => r["_measurement"] == "controller_config" and r["_field"] == "control_sensor") |> last()'
        tables = await asyncio.to_thread(query_api.query, flux)
        if tables and len(tables) > 0 and len(tables[0].records) > 0:
            val = tables[0].records[0].get_value()
            if val in SENSOR_OPTIONS:
                async with control_sensor_lock:
                    global control_sensor_name
                    control_sensor_name = val
                logging.info(f"Loaded control sensor from InfluxDB: {val}")
            else:
                logging.warning(f"Influx control_sensor value not in SENSOR_OPTIONS: {val}")
    except Exception:
        logging.exception("failed to load control sensor from influx")

async def kasa_worker(q ,influx_q):
    # single worker that serializes kasa device access and state changes
    plug = SmartPlug(heater_ip)
    await plug.update()
    heater_on = plug.is_on
    logging.info(f"Initial Plug state : {'ON' if heater_on else 'OFF'}")
    # send heater state to influx
    point = (
        Point('heater_state')
        .tag("location", 'garage')
        .field("heater_on", 1 if heater_on else 0)
    )
    await influx_q.put(point)

    RATE_LIMIT_SECONDS = 60 * 60  # 1 hour rate limit between state changes
    last_on_time = 0
    last_off_time = 0

    while True:
        sensor_name, temperature_degF = await q.get() # wait for new temperature reading from MQTT
        logging.info(f"Worker processing temperature for {sensor_name}: {temperature_degF}°F")
        await plug.update()
        prev_state = heater_on
        heater_on = plug.is_on
        
        # Always publish heater state to InfluxDB
        point = (
            Point('heater_state')
            .tag("location", 'garage')
            .field("heater_on", 1 if heater_on else 0)
        )
        await influx_q.put(point)
        
        if heater_on != prev_state:
            logging.info(f"Detected state changed from outside source! heater_on={heater_on}")
            if heater_on:
                last_on_time = monotonic()
            else:
                last_off_time = monotonic()
        logging.info(f"Current Plug state : {'ON' if heater_on else 'OFF'}")

        async with thresholds_lock:
            on_thresh = thresholds['on']
            off_thresh = thresholds['off']
            logging.info(f"Using thresholds: ON={on_thresh}°F, OFF={off_thresh}°F")


        try:
            async with control_sensor_lock:
                current_control = control_sensor_name
            if sensor_name == current_control:
                now = monotonic() # current time in seconds
                if temperature_degF < on_thresh and not heater_on:
                    if now - last_on_time >= RATE_LIMIT_SECONDS:
                        logging.info("Heater ON (worker)")
                        await plug.turn_on()
                        heater_on = True
                        last_on_time = now
                    else:
                        logging.info(f"Skipping turn_on; last on {int(now - last_on_time)}s ago")
                elif temperature_degF > off_thresh and heater_on:
                    if now - last_off_time >= RATE_LIMIT_SECONDS:
                        logging.info("Heater OFF (worker)")
                        await plug.turn_off()
                        heater_on = False
                        last_off_time = now
                    else:
                        logging.info(f"Skipping turn_off; last off {int(now - last_off_time)}s ago")

            
                # if state changed, enqueue InfluxDB write
                if heater_on != prev_state:
                    logging.info(f"State changed by control logic: heater_on={heater_on}")
        except Exception:
            logging.exception("kasa worker error")
        finally:
            q.task_done()

async def influx_worker(influx_q):
    # single writer that performs blocking InfluxDB writes in a thread
    while True:
        point = await influx_q.get()
        try:
            # write_api is blocking; run in default threadpool
            await asyncio.to_thread(write_api.write, bucket=bucket, org=org, record=point)
        except Exception:
            logging.exception("influx write failed")
        finally:
            influx_q.task_done()

async def config_publisher(influx_q):
    # periodically publish threshold and control sensor settings to influx
    while True:
        try:
            logging.debug("Publishing config to InfluxDB...")
            async with thresholds_lock:
                on_thresh = thresholds['on']
                off_thresh = thresholds['off']
            async with control_sensor_lock:
                current_control = control_sensor_name
            
            # publish thresholds
            point_on = (
                Point('controller_config')
                .tag('location', 'heater')
                .field('threshold_on', on_thresh)
            )
            await influx_q.put(point_on)
            
            point_off = (
                Point('controller_config')
                .tag('location', 'heater')
                .field('threshold_off', off_thresh)
            )
            await influx_q.put(point_off)
            
            # publish control sensor
            point_control = (
                Point('controller_config')
                .tag('location', 'heater')
                .field('control_sensor', current_control)
            )
            await influx_q.put(point_control)
            
            logging.debug(f"Published config to influx: thresholds on={on_thresh} off={off_thresh}, control_sensor={current_control}")
        except Exception:
            logging.exception("config publisher error")
        
        # publish every 60 seconds
        await asyncio.sleep(60)

async def handle_messages():
    sensor_q = asyncio.Queue()
    influx_q = asyncio.Queue()
    # start workers
    worker_task = asyncio.create_task(kasa_worker(sensor_q, influx_q))
    influx_task = asyncio.create_task(influx_worker(influx_q))
    config_publisher_task = asyncio.create_task(config_publisher(influx_q))

    # start REST server
    rest_runner = await start_rest_server(host='0.0.0.0', port=8000, influx_q=influx_q)

    # load persisted control sensor from InfluxDB (if present)
    await load_control_sensor_from_influx()

    try:
        async with AIOMQTT(hostname=mqtt_broker_ip, port=1883, username=mqtt_username, password=mqtt_password) as client:
            async with client.messages() as messages:
                await client.subscribe(temperature_topic)
                async for msg in messages:
                    topic = str(msg.topic)
                    payload = msg.payload.decode()
                    try:
                        parts = topic.split('/')
                        if len(parts) == 2 and parts[0] == "temperature_degC":
                            sensor_name = parts[1]
                            temp_f = celsius_to_fahrenheit(float(payload))
                            await sensor_q.put((sensor_name, temp_f))
                    except Exception:
                        logging.exception("message handling error")
    finally:
        await sensor_q.join()
        await influx_q.join()
        worker_task.cancel()
        influx_task.cancel()
        config_publisher_task.cancel()
        await rest_runner.cleanup()


asyncio.run(handle_messages())

