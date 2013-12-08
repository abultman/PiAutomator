"""
This input module supports getting data from PiLight (http://http://www.pilight.org/) and triggering rules accordingly
"""
import socket
import json
import logging
import threading
from inputs.inputs import AnInput

pilight_sensors = {}
__logger__ = logging.getLogger('pilight-receiver')
__logger__.setLevel(logging.INFO)

def init(config):
    """
    Initializes the pilight receiver connection. Sets up a heartbeat

    @type config: config.AutomationConfig
    """
    receiver = PiLightDaemon('127.0.0.1', 5000)
    worker_thread = threading.Thread(target=receiver.receive)
    worker_thread.daemon = True
    worker_thread.start()

class PiLight(AnInput):
    def __init__(self, name, settings, g):
        self.room = settings['room']
        self.input = settings['input']
        self.scale = settings['scale']
        self.values = None
        pilight_sensors["%s.%s" %(self.room, self.input)] = self

    def update(self, data):
        self.values = data['values']

    def _read(self):
        if self.values:
            result = {}
            for key in self.values:
                result[key] = float(self.values[key]) * self.scale
            return result
        else:
            return None

class PiLightDaemon(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.open()
        self.current_buffer = ""

    def open(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.socket.send(json.dumps({'message': 'client gui'}))
        print "inited"
        __logger__.info("connected to pilight as a receiver")

    def receive(self):
        while True:
            msg = self.socket.recv(12)
            self.current_buffer = "%s%s" %(self.current_buffer, msg)
            self.find_messages()

    def find_messages(self):
        new_buffer = ""
        for message in self.current_buffer.splitlines(True):
            if message.endswith('\n'):
                self.process_message(message)
            else:
                new_buffer = message
        self.current_buffer = new_buffer

    def process_message(self, messagestr):
        __logger__.debug(messagestr)
        message = json.loads(messagestr)
        if 'devices' in message:
            devices = message['devices']
            for device in devices:
                inputs = devices[device]
                for input in inputs:
                    key = "%s.%s" % (device, input)
                    if key in pilight_sensors:
                        pilight_sensors[key].update(message)

