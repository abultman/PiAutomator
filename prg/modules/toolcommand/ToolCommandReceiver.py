import Queue
import threading
import logging
import subprocess

from receivers import *
from receivers.receivers import Receiver


jobqueue = Queue.Queue()

__logger__ = logging.getLogger("tool-command-receiver")
__logger__.setLevel(logging.INFO)


def init_module():
    def __worker_main__():
        while True:
            toexec = jobqueue.get()
            __logger__.info(toexec)
            subprocess.call(toexec, shell=True)

    worker_thread = threading.Thread(target=__worker_main__, name='subprocess-command-executor')
    worker_thread.daemon = True
    worker_thread.start()


class ToolCommandReceiver(Receiver):
    def __init__(self, name, context, settings):
        super(ToolCommandReceiver, self).__init__(name, context, settings)
        self.intools = settings.getsetting('intools', True)

    def perform_for_state(self, verb, state):
        command = None
        if self.intools:
            command = "%s/tools/%s" % (self.config.get_basedir(), self.settings['command'])
        else:
            command = self.settings['command']
        args = self.settings['args'].replace("${state}", state).replace("${name}", self.name).replace("${verb}", verb)
        toexec = "%s %s" % (command, args)
        __logger__.debug(toexec)
        jobqueue.put(toexec)

