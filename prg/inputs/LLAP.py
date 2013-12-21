"""
This input module supports getting data from pilight (http://http://www.pilight.org/) and triggering rules accordingly
"""
from itertools import dropwhile
from Queue import Queue
import logging
import tempfile
import threading
import re
import serial
import sys
import time
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

llap_hello_cmds = ['HELLO', 'STARTED', 'AWAKE']

global llap_receiver

def init(config):
    """
    Initializes the pilight receiver connection. Sets up a heartbeat

    @type config: config.AutomationConfig
    """
    global llap_receiver

    llap_receiver = LLAPDaemon(
        config.getSetting(['llap','device'], '/dev/ttyAMA0'),
        config.getSetting(['llap','print-debug'], False)
    )


class LLAP(AnInput):
    def __init__(self,  name, context, settings):
        super(LLAP, self).__init__(name, context, settings)
        self.device_id = settings['device-id']
        self.values = None
        self.cycle = settings.getsetting('cycle', False)
        self.cycle_period = settings.getsetting('cycle-period', '005S')
        self.read_command = settings.getsetting('read-command', 'TEMP')
        lllap_sensors[self.device_id] = self

    def update(self, sentcommand):
        if not self.started: return
        __logger__.debug("update: " + sentcommand)
        if self.cycle:
            for command in llap_hello_cmds:
                if sentcommand.startswith(command):
                    self.send("ACK")
                    self.send(self.read_command)
                    self.send("BATT")
                    self.send("SLEEP" + self.cycle_period)

        for command in sorted(llap_commands, key=lambda x: len(x), reverse=True):
            if sentcommand.startswith(command):
                value = sentcommand[len(command):]
                key = llap_commands[command][0]
                converter = llap_commands[command][1]
                self.publish({key: converter(value)})
                return

    def send(self, message):
        llap_receiver.send(("a" + self.device_id + message).ljust(12,'-'))

    def start(self):
        super(LLAP, self).start()
        if self.cycle:
            # Say hello, show get a response from the other end
            self.send("HELLO")

class LLAPDaemon(object):
    def __init__(self, device, debug):
        self.p = re.compile('a[A-Z][A-Z][A-Z0-9.-]{9,}.*')
        self.ser = serial.Serial(device, 9600)
        self.debug = debug
        self.current_buffer = ""
        if (debug):
            self.debug_file = tempfile.NamedTemporaryFile()
            __logger__.info("Debugging serial input to %s", self.debug_file.name)
            self.debug_file.write("----- Serial input debug file -----\n")
            self.debug_file.flush()

        self.send_queue = Queue()
        thread = threading.Thread(target=self.receive)
        thread.daemon = True
        thread.start()
        thread = threading.Thread(target=self.__send__)
        thread.daemon = True
        thread.start()


    def send(self, message):
        self.send_queue.put(message)

    def __send__(self):
        while True:
            message = self.send_queue.get()
            try:
                __logger__.debug("Sending: " + message)
                self.ser.write(message)
                # Wait some time, since command that go too quick seem to be a problem
                time.sleep(0.05)
            except:
                __logger__.exception(sys.exc_info()[0])
                __logger__.warn("exception happened")

    def receive(self):
        __logger__.info("Starting in receiving mode for llap")
        try:
            while True:
                self.current_buffer += self.__read__(1)
                n = self.ser.inWaiting()
                if (n > 0):
                    self.current_buffer += self.__read__(n)
                self.find_messages()
        except:
            __logger__.exception(sys.exc_info()[0])
            __logger__.warn("exception happened")

    def __read__(self, size):
        result = self.ser.read(size)
        if self.debug:
            # Nice thing about tmp files is that Python will clean them on
            # system close
            self.debug_file.write(result)
            self.debug_file.flush()
        return result

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
        except:
            __logger__.exception(sys.exc_info()[0])
            __logger__.warn("exception happened")

    def process_device_message(self, message):
        device = message[1:3]
        command = message[3:].replace('-','')
        if command.startswith("CHDEVID"):
            __logger__.info("We were asked to change our device id, but we're only listening:), %s", command)
        elif device in lllap_sensors:
            llap_sensor = lllap_sensors[device]
            llap_sensor.update(command)
