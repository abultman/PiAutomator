#!/usr/bin/python

import os
import time
import signal
import logging

import dhtreader
import receivers
import inputs
import schedule
import rules
from config import AutomationConfig


logging.basicConfig(format = '%(asctime)s - %(levelname)s - %(message)s')
basedir = os.path.normpath("%s/.." % (os.path.dirname(os.path.abspath(__file__))))

# Initialize all components
config = AutomationConfig(basedir)
receivers = receivers.init(config)
inputs = inputs.init(config)
allrules = rules.init(config, inputs, receivers)

# Setup the handler that will terminate our event loops.
global running
running = True
def signal_handler(signal, frame):
  global running
  running = False
  print 'Terminating'

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Run the ticktock
while(running):
  schedule.run_pending()
  time.sleep(1)
