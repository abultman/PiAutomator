from logging.handlers import RotatingFileHandler
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
config = AutomationConfig(basedir)

log_format = config.get_setting(['automator', 'logging', 'format'], '%(asctime)s - %(levelname)s - %(name)s - %(message)s')
log_destination = config.get_setting(['automator', 'logging', 'destination'], 'file')

if log_destination == 'file':
    logs_basedir = "%s/logs" % basedir
    if not os.path.exists(logs_basedir):
        os.mkdir(logs_basedir)
    logfile = "%s/piautomator.log" % logs_basedir
    formatting = logging.Formatter(log_format, None)
    handler = RotatingFileHandler(logfile, maxBytes=1024 * 1024 * 100, backupCount=3)
    handler.setFormatter(formatting)
    logging.root.addHandler(handler)
else:
    logging.basicConfig(format=log_format)

# Initialize all components
global automation_context
automation_context = AutomationContext(config)
automation_context.receivers = receivers.init(automation_context)
automation_context.inputs = inputs.init(automation_context)
automation_context.rule_context = rules.init(automation_context)

automation_context.start()

# Setup the handler that will terminate our event loops.
global running
running = True

def signal_handler(signal, frame):
    global running
    running = False
    automation_context.stop()
    print 'Terminated'


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Run the ticktock
while (running):
    schedule.run_pending()
    time.sleep(1)
