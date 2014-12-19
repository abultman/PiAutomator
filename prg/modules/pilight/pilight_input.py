"""
This input module supports getting data from pilight (http://http://www.pilight.org/) and triggering rules accordingly
"""
import socket
import json
import logging
import threading
import time
from config import LocalSettings
from inputs.inputs import AnInput

pilight_sensors = {}
__logger__ = logging.getLogger('pilight-receiver')
__logger__.setLevel(logging.INFO)

def init_module(config):
    """
    Initializes the pilight receiver connection. Sets up a heartbeat

    @type config: config.AutomationConfig
    """
    pilightDaemon(
        config.get_setting(['pilight', 'host'], '127.0.0.1'),
        config.get_setting(['pilight', 'port'], 5000),
        config.get_setting(['pilight', 'rawprotocols'], []))

class pilight_input(AnInput):
    def __init__(self,  name, context, settings):
        super(pilight_input, self).__init__(name, context, settings)
        self.room = settings['location']
        self.input = settings['device']
        self.scale = settings['scale']
        self.values = None
        pilight_sensors["%s.%s" %(self.room, self.input)] = self

    def __get_values__(self, origvalues):
        values = {}
        for key in origvalues:
            if origvalues[key] in ['on', 'up']:
                values[key + '_int'] = 1
            elif origvalues[key] in ['off', 'down']:
                values[key + '_int'] = 0
            values[key] = origvalues[key]
        return values

    def update(self, data, publish_key = None):
        if not self.started: return
        if publish_key == 'raw':
            self.update_raw(data)
        else:
            origvalues = data['values']
            values = self.__get_values__(origvalues)
            if publish_key:
                self.publish(values, 'pilight.%s' % (publish_key))
            elif self.scale:
                result = {}
                for key in values:
                    result[key] = float(values[key]) * self.scale
                self.publish(result)
            else:
                self.publish(values)

    def update_raw(self, data):
        # {"code":{"id":11449862,"unit":0,"state":"up"},"origin":"receiver","protocol":"archtech_screens","repeats":2}
        __logger__.debug(data)
        if 'protocol' in data and 'code' in data:
            try:
                wrapped_data = LocalSettings(data['code'])
                protocol = data['protocol']
                id = wrapped_data.getsetting('id', 'noid')
                unit = wrapped_data.getsetting('unit', 'nounit')
                publish_key = 'pilight.raw.%s.%s.%s' % (protocol, id, unit)
                values = self.__get_values__(data['code'])
                self.publish(values, publish_key)
            except Exception, e:
                print e

class pilightDaemon(object):
    def __init__(self, host, port, raw_protocols):
        """
        @type raw_protocols list
        """
        self.host = host
        self.port = port
        self.current_buffer = ""
        self.current_buffer_raw = ""
        self.raw_protocols = raw_protocols
        pilightthread = threading.Thread(target=self.receive, name='pilight-receiver')
        pilightthread.daemon = True
        pilightthread.start()
        if len(raw_protocols) > 0:
            for p in raw_protocols:
                __logger__.info("raw protocol %s will be supported", p)
            pilightthread = threading.Thread(target=self.receive_raw, name='pilight-receiver-raw')
            pilightthread.daemon = True
            pilightthread.start()

    def connect_raw(self):
        try:
            self.socket_raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_raw.connect((self.host, self.port))
            self.socket_raw.send(json.dumps({'message': 'client receiver'}))
            __logger__.info("Starting in receiving mode for pilight raw")
        except:
            self.socket_raw = None

    def connect_gui(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.send(json.dumps({'message': 'client gui'}))
            self.socket.send(json.dumps({'message': 'request config'}))
            self.send_to_all({'values': {'state': 'up'}}, 'connection')
            __logger__.info("Starting in receiving mode for pilight")
        except:
            self.socket = None

    def receive_raw(self):
        def close():
            try:
                self.socket_raw.close()
            except:
                pass
            self.socket_raw = None
            __logger__.info("raw input terminated, pilight down?")

        while True:
            self.connect_raw()
            while self.socket_raw is not None:
                try:
                    msg = self.socket_raw.recv(1024)
                    if len(msg) == 0:
                        close()
                    else:
                        self.current_buffer_raw = "%s%s" %(self.current_buffer_raw, msg)
                        self.current_buffer_raw = self.find_messages(self.current_buffer_raw)
                except:
                    close()

            time.sleep(2)

    def receive(self):
        def close():
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            self.send_to_all({'values': {'state': 'down'}}, 'connection')
            __logger__.info("raw input terminated, pilight down?")

        while True:
            self.connect_gui()
            while self.socket is not None:
                try:
                    msg = self.socket.recv(1024)
                    if len(msg) == 0:
                        close()
                    else:
                        self.current_buffer = "%s%s" %(self.current_buffer, msg)
                        self.current_buffer = self.find_messages(self.current_buffer)
                except:
                    close()
            time.sleep(2)


    def find_messages(self, buffer):
        try:
            new_buffer = ""
            for message in buffer.splitlines(True):
                if message.endswith('\n'):
                    self.process_message(message)
                else:
                    new_buffer = message
            return new_buffer
        except Exception, e:
            __logger__.warn("exception happened")
            __logger__.exception(e)
            return buffer

    def process_device_message(self, message):
        devices = message['devices']
        for device in devices:
            inputs = devices[device]
            for input in inputs:
                key = "%s.%s" % (device, input)
                if key in pilight_sensors:
                    pilight_sensors[key].update(message)
                else:
                    self.send_to_all(message, key)

    def process_raw_message(self, message):
        if 'protocol' in message and message['protocol'] in self.raw_protocols:
            self.send_to_all(message, 'raw')

    def process_config_message(self, message):
        config = message['config']
        __logger__.info("Configuration of pilight\n%s", config)

    def process_message(self, messagestr):
        try:
            if messagestr == '\n': return
            __logger__.debug("message: '" + messagestr + "'")
            message = json.loads(messagestr)
            if 'devices' in message:
                self.process_device_message(message)
            elif 'config' in message:
                self.process_config_message(message)
            else:
                self.process_raw_message(message)
        except Exception, e:
            __logger__.error("Exception while processing message")
            __logger__.error(messagestr)
            __logger__.error(e)
            raise e

    def send_to_all(self, message, key):
        if 'all.all' in pilight_sensors:
            pilight_sensors['all.all'].update(message, key)
