#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# check_host_temperature.py
# This file is part of epol/vmware-scripts
#
# Copyright (C) 2018 - Enrico Polesel
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import argparse
import logging
import pyVim.connect
import atexit

parser = argparse.ArgumentParser()
parser.add_argument("-vc","--vcenter", help="Vcenter hostname",required=True)
parser.add_argument("-u","--username", help="Username", required=True)
parser.add_argument("-p","--password", help="User password", required=True)
parser.add_argument("-hn","--hostname", help="vpshere host DNS name",required=True)
parser.add_argument("-n","--sensorname", help="Sensor name", required=True)
parser.add_argument("-ll", "--log-level", help="Logger log level",required=False)

args = parser.parse_args()

logger = logging.getLogger(sys.argv[0])
logger.propagate = False
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)-9s %(levelname)-8s %(message)s',datefmt='%H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
if args.log_level is not None:
    logger.setLevel(args.log_level)
else:
    logger.setLevel('CRITICAL')


logger.debug("Opening connection to vcenter")
SI=None
try:
    SI = pyVim.connect.SmartConnectNoSSL(host=args.vcenter,
                                         user=args.username,
                                         pwd=args.password)
    logger.debug("Registering disconnect")
    atexit.register(pyVim.connect.Disconnect,SI)
except IOError as ex:
    pass

if not SI:
    logger.info("Unable to open the connection to vcenter")
    print("UNKNOWN - Unable to open the connection to vcenter")
    sys.exit(3)
logger.info("Connection established")

logger.debug("Looking for host with DnsName {hostname}".format(hostname=args.hostname))
host = SI.content.searchIndex.FindByDnsName(None,args.hostname,False)
if not host:
    logger.info("Unable to find host {hostname}".format(hostname=args.hostname))
    print("UNKNOWN - Unable to find host {hostname}".format(hostname=args.hostname))
    sys.exit(3)
logger.info("Host found")
logger.debug("Host model: {model}".format(model=host.hardware.systemInfo.model))

health = host.runtime.healthSystemRuntime.systemHealthInfo.numericSensorInfo

logger.debug("Looking for sensor")
sensor = None
for i in health:
    if i.sensorType == "temperature" and i.name.startswith(args.sensorname):
        sensor = i
        break
if not sensor:
    logger.info("Temperature sensor named {name} not found".format(name=args.sensorname))
    print ("UNKNOWN - Unable to find temperature sensor named {name}".format(name=args.sensorname))
    sys.exit(3)

temperature = sensor.currentReading * 10**(sensor.unitModifier)

logger.debug("Sensor healthState is {state}".format(state=sensor.healthState.key))
if sensor.healthState.key == "green":
    state = "OK"
    returncode = 0
elif sensor.healthState.key == "yellow":
    state = "WARNING"
    returncode = 1
elif sensor.healthState.key == "red":
    state = "CRITICAL"
    returncode = 2
elif sensor.healthState.key == "unknown":
    state = "UNKNOWN"
    returncode = 3
else:
    state = "UNKNOWN"
    returncode = 3

print("{state} - Host {hostname} temperature sensor {name} reading is {temperature} {unit}|temperature={temperature}".format(state=state,hostname=host.name,name=sensor.name,temperature=temperature,unit=sensor.baseUnits))
sys.exit(returncode)

