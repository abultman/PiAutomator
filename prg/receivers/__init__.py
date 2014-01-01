from core import SCOPE_RECEIVER, load_class
from config import LocalSettings

from graphitereporter import *

__myclasses__ = {}

__logger__ = logging.getLogger("recievers")
__logger__.setLevel(logging.INFO)


def __load_receiver__(elem, config):
    return load_class(elem, config, SCOPE_RECEIVER)

def init(context):
    # g = GraphiteReporter(config, "receivers")
    receiverInstances = Receivers()
    receivers = context.config.receivers()
    for name in receivers:
        my_class = __load_receiver__(receivers[name]['type'], context.config)
        receiverInstances.addReceiver(my_class(name, context, LocalSettings(receivers[name])))

    # schedule.every(10).seconds.do(receiverInstances.reportToGraphite)

    return receiverInstances


class Receivers(object):
    def __init__(self, receivers={}):
        self.receivers = receivers
        self.started = False

    def addReceiver(self, receiver):
        """
        @type receiver: receivers.Receiver
        """
        self.receivers[receiver.name] = receiver
        if self.started:
            receiver.start()

    def start(self):
        self.started = True
        [recv.start() for recv in self.receivers.values()]
        __logger__.info("Receivers started")

    def stop(self):
        [recv.stop() for recv in self.receivers.values()]
        __logger__.info("Receivers stopped")

    def reportToGraphite(self):
        for receiver in self.receivers.values():
            receiver._sendForReporting()

    def __getitem__(self, key):
        return self.receivers[key]