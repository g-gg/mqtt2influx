#!/usr/bin/python3

import paho.mqtt.client as mqtt
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import json
from dotenv import load_dotenv
import os
import logging
import sys
from systemd import journal # requires apt install python3-systemd

load_dotenv()

influx_bucket = os.getenv('INFLUX_BUCKET')
influx_org = os.getenv('INFLUX_ORG')
influx_token = os.getenv('INFLUX_TOKEN')
influx_url = os.getenv('INFLUX_URL')
mqtt_url = os.getenv('MQTT_URL')
mqtt_port = os.environ.get("MQTT_PORT", 1883)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    mqtt_client.subscribe("zigbee2mqtt/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    topics = msg.topic.split('/')
    if msg.topic.startswith('zigbee2mqtt/bridge'):
        pass
    elif len(topics) == 2:
        device = topics[1].strip()
        try:
            payload = json.loads(msg.payload)
            logger.debug(f'received and parsed message from {device}: {payload}')
        except:
            logger.error(f'error parsing message on topic {msg.topic}')

        p = dict()
        p['measurement'] = device
        p['fields'] = payload

        try:
            influx_write_api.write(bucket=influx_bucket, org=influx_org, record=p, write_precision='s')
        except:
            logger.error(f'error sending message to influx {p}')
    else:
        print(msg.topic+" "+str(msg.payload))

logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

journald_handler = journal.JournalHandler(SYSLOG_IDENTIFIER=__name__)
journald_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
logger.addHandler(journald_handler)

logger.setLevel(logging.DEBUG)

influx_client = influxdb_client.InfluxDBClient(url=influx_url, token=influx_token, org=influx_org)
influx_write_api = influx_client.write_api(write_options=SYNCHRONOUS)

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(mqtt_url, mqtt_port, 60)
logger.info(f'connected to mqtt broker {mqtt_url}:{mqtt_port}')

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
mqtt_client.loop_forever()
