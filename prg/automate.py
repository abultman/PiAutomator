import os
import time
import signal
import logging

import schedule
from context import AutomationContext

import receivers
import inputs
import rules
from config import AutomationConfig

basedir = os.path.normpath("%s/.." % (os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize all components
config = AutomationConfig(basedir)
context = AutomationContext(config)
inputs = inputs.init(context)
context.receivers = receivers.init(context)
context.rule_context = rules.init(context)

context.start()

# Setup the handler that will terminate our event loops.
global running
running = True

def signal_handler(signal, frame):
    global running
    running = False
    context.stop()
    print 'Terminating'


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Run the ticktock
while (running):
    schedule.run_pending()
    time.sleep(1)
