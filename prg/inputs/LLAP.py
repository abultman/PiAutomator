"""
This input module supports getting data from pilight (http://http://www.pilight.org/) and triggering rules accordingly
"""
from itertools import dropwhile
import logging
import threading
import re
import serial
from inputs import AnInput

def _true(value = None):
    return True

def _false(value = None):
    return False

lllap_sensors = {}
__logger__ = logging.getLogger('llap-receiver')
__logger__.setLevel(logging.INFO)

llap_commands = {
    'BATTLOW': ['lowbattery', _true],
    'BATT': ['batterylevel', float],
    'STARTED': ['lowbattery', _false],
    'LVAL': ['lightlevel', float],
    'TEMP': ['temperature', float],
    'TMPA': ['temperature', float],
    'ANA': ['analog', int],
    'BUTTON': ['button', str]
}

def init(config):
    """
    Initializes the pilight receiver connection. Sets up a heartbeat

    @type config: config.AutomationConfig
    """
    receiver = LLAPDaemon()
    thread = threading.Thread(target=receiver.receive)
    thread.daemon = True
    thread.start()

class LLAP(AnInput):
    def __init__(self,  name, context, settings):
        super(LLAP, self).__init__(name, context, settings)
        self.device_id = settings['device-id']
        self.values = None
        lllap_sensors[self.device_id] = self

    def update(self, sentcommand):
        if not self.started: return
        for command in sorted(llap_commands, key=lambda x: len(x), reverse=True):
            if sentcommand.startswith(command):
                value = sentcommand[len(command):]
                key = llap_commands[command][0]
                converter = llap_commands[command][1]
                self.publish({key: converter(value)})
                return

class LLAPDaemon(object):
    def __init__(self):
        self.p = re.compile('a[A-Z][A-Z][A-Z0-9.-]{9,}.*')

    def open(self):
        self.ser = serial.Serial("/dev/ttyAMA0", 9600)

    def receive(self):
        __logger__.info("Starting in receiving mode for llap")
        while True:
            n = self.ser.inWaiting()
            if (n > 0):
                self.current_buffer += self.ser.read(n)

    def find_messages(self):
        try:
            self.current_buffer = ''.join(dropwhile(lambda x: not x == 'a', (i for i in self.current_buffer)))
            if len(self.current_buffer) >= 12:  # 12 is the LLAP message length
                 if self.p.match(self.current_buffer):
                     self.process_device_message(self.current_buffer[0:12])
                     self.current_buffer = self.current_buffer[12:]
                 else:
                     self.current_buffer = self.current_buffer[1:]
                     self.find_messages()

            self.find_messages()
            new_buffer = ""
            for message in self.current_buffer.splitlines(True):
                if message.endswith('\n'):
                    self.process_message(message)
                else:
                    new_buffer = message
            self.current_buffer = new_buffer
        except:
            __logger__.warn("exception happened")

    def process_device_message(self, message):
        device = message[1:3]
        command = message[3:].replace('-','')
        if command == 'HELLO':
            __logger__.info("%s said hello", device)
        elif command.startswith("CHDEVID"):
            __logger__.info("We were asked to change our device id, but we're only listening:), %s", command)
        elif device in lllap_sensors:
            llap_sensor = lllap_sensors[device]
            llap_sensor.update(llap_sensor)