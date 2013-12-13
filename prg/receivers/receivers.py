import logging


class StateError(Exception):
    pass

__logger__ = logging.getLogger("receiver")
__logger__.setLevel(logging.INFO)

class Receiver(object):
    def __init__(self, name, context, settings):
        """
        @type context: context.AutomationContext
        """
        self.settings = settings
        self.name = name
        self.any_state = settings.getsetting("any-state", False)
        self.maintain_state = settings.getsetting("maintain-state", True)
        self.context = context

    def do(self, verb, incoming_state, override=False):
        if (not self.any_state and incoming_state not in self.supported_states()):
            raise StateError("Illegal state passed to set. %s not in %s" % (incoming_state, self.supported_states()))

        if override or not self.overrideMode():
            state = self.get_state()
            if not self.maintain_state or state != incoming_state or state == None:
                self.perform_for_state(verb, incoming_state)
                __logger__.info("%s %s %s" % (verb, self.name, incoming_state))
                self.set_state(incoming_state)
        else:
            logging.debug(
                "Receiver %s is in override mode, only rules with override can change it's state now" % self.name)

    def overrideMode(self):
        return self.context.getReceiverValue(self.name + ".overridemode")

    def setOverrideMode(self, override):
        self.context.publishReceiverValues(self.name, {'overridemode' : override})
        if override:
            logging.warn("Receiver %s just went into override mode" % self.name)
        else:
            logging.warn("Receiver %s just went out of override mode" % self.name)

    def supported_states(self):
        return ["off", "on"]

    def _getForReporting(self):
        if (not self.any_state):
            value = -1
            state = self.get_state()
            if state:
                value = self.supported_states().index(state)
            return value
        return -1

    def perform_for_state(self, verb, state):
        None

    def get_state(self):
        return self.context.getReceiverValue(self.name + ".state")

    def set_state(self, state):
        self.context.publishReceiverValues(self.name, {
                "state": state,
                "state_int": self._getForReporting()
            }
        )


