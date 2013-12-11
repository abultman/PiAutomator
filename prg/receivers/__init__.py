import schedule

from graphitereporter import *

__myclasses__ = {}

__logger__ = logging.getLogger("recievers")
__logger__.setLevel(logging.INFO)


def __load_receiver__(elem, config):
    if elem not in __myclasses__:
        __logger__.info("Loading receiver of type %s" % elem)
        mod = __import__(elem, globals=globals())
        __myclasses__[elem] = getattr(mod, elem)
        if hasattr(mod, 'init'):
            getattr(mod, 'init')(config)
            __logger__.info("Initializing %s" % elem)

    return __myclasses__[elem]


def init(context):
    # g = GraphiteReporter(config, "receivers")
    receiverInstances = Receivers()
    receivers = context.config.receivers()
    for name in receivers:
        my_class = __load_receiver__(receivers[name]['type'], context.config)
        receiverInstances.addReceiver(my_class(name, context, receivers[name]))

    # schedule.every(10).seconds.do(receiverInstances.reportToGraphite)

    return receiverInstances


class Receivers(object):
    def __init__(self, receivers={}):
        self.receivers = receivers

    def addReceiver(self, receiver):
        """
        @type receiver: receivers.Receiver
        """
        self.receivers[receiver.name] = receiver

    def reportToGraphite(self):
        for receiver in self.receivers.values():
            receiver._sendForReporting()

    def __getitem__(self, key):
        return self.receivers[key]