#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# check_guest_powerstate.py
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
parser.add_argument("-i","--uuid", help="Guest UUID")
parser.add_argument("-H","--hostname", help="Vsphere hostname",required=True)
parser.add_argument("-u","--username", help="Username", required=True)
parser.add_argument("-p","--password", help="User password", required=True)
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


logger.debug("Opening connection to vsphere")
SI=None
try:
    SI = pyVim.connect.SmartConnectNoSSL(host=args.hostname,
                                         user=args.username,
                                         pwd=args.password)
    logger.debug("Registering disconnect")
    atexit.register(pyVim.connect.Disconnect,SI)
except IOError as ex:
    pass

if not SI:
    logger.critical("Unable to open the connection to vsphere")
    print("UNKNOWN - Unable to open the connection to vsphere")
    sys.exit(3)
logger.info("Connection established")

logger.debug("Looking for guest with UUID {uuid}".format(uuid=args.uuid))
VM = SI.content.searchIndex.FindByUuid(None,args.uuid,True,False)
logger.info("Found guest named {name}".format(name=VM.name))
powerState = VM.runtime.powerState
logger.debug("powerState is {powerState}".format(powerState=powerState))
if powerState=="poweredOn":
    status = "OK"
    exitcode = 0
elif powerState=="poweredOff":
    status = "CRITICAL"
    exitcode = 2
else:
    status = "UNKNOWN"
    exitcode = 3
print("{status} - Guest {name} powerstate is {powerState}".format(status=status,name=VM.name,powerState=powerState))
sys.exit(exitcode)

