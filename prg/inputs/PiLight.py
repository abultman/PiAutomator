"""
This input module supports getting data from pilight (http://http://www.pilight.org/) and triggering rules accordingly
"""
import socket
import json
import logging
import threading
from inputs import AnInput

pilight_sensors = {}
__logger__ = logging.getLogger('pilight-receiver')
__logger__.setLevel(logging.INFO)

def init(config):
    """
    Initializes the pilight receiver connection. Sets up a heartbeat

    @type config: config.AutomationConfig
    """
    receiver = PiLightDaemon(
        config.getSetting(['pilight', 'host'], '127.0.0.1'),
        config.getSetting(['pilight', 'port'], 5000))
    worker_thread = threading.Thread(target=receiver.receive)
    worker_thread.daemon = True
    worker_thread.start()

class PiLight(AnInput):
    def __init__(self,  name, context, settings):
        super(PiLight, self).__init__(name, context, settings)
        self.room = settings['location']
        self.input = settings['device']
        self.scale = settings['scale']
        self.values = None
        pilight_sensors["%s.%s" %(self.room, self.input)] = self

    def update(self, data, publish_key = None):
        if not self.started: return
        origvalues = data['values']
        values = {}
        for key in origvalues:
            if origvalues[key] in ['on', 'up']:values[key+'_int'] = 1
            elif origvalues[key] in ['off', 'down']:values[key+'_int'] = 0
            values[key] = origvalues[key]
        if publish_key:
            self.publish(values, 'pilight.%s' % (publish_key))
        elif self.scale:
            result = {}
            for key in values:
                result[key] = float(values[key]) * self.scale
            self.publish(result)
        else:
            self.publish(values)

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
        __logger__.info("connected to pilight as a receiver")
        self.socket.send(json.dumps({'message': 'request config'}))
        self.socket.recv

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

    def process_device_message(self, message):
        devices = message['devices']
        for device in devices:
            inputs = devices[device]
            for input in inputs:
                key = "%s.%s" % (device, input)
                if key in pilight_sensors:
                    pilight_sensors[key].update(message)
                elif 'all.all' in pilight_sensors:
                    pilight_sensors['all.all'].update(message, key)


    def process_config_message(self, message):
        config = message['config']
        __logger__.debug("Configuration of pilight\n%s", json.dumps(config, indent=2).encode('utf-8'))


    def process_message(self, messagestr):
        __logger__.debug(messagestr)
        message = json.loads(messagestr)
        if 'devices' in message:
            self.process_device_message(message)
        if 'config' in message:
            self.process_config_message(message)

