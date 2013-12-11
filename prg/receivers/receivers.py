import logging


class StateError(Exception):
    pass


class Receiver(object):
    def __init__(self, name, context, settings):
        """
        @type context: context.AutomationContext
        """
        self.settings = settings
        self.name = name
        self.state = None
        self.overrideMode = False
        self.any_state = "any-state" in settings and settings["any-state"]
        self.maintain_state = not "maintain-state" in settings or settings["maintain-state"]
        self.context = context

    def do(self, verb, switch, override=False):
        if (not self.any_state and switch not in self.supported_states()):
            raise StateError("Illegal state passed to set. %s not in %s" % (switch, self.supported_states()))

        if override or not self.overrideMode:
            if not self.maintain_state or self.state != switch or self.state == None:
                self._setState(verb, switch)
                logging.warn("%s %s %s %s %s" % (verb, self.name, switch, self.state, self.maintain_state ))
                self.state = switch
                self.context.publishReceiverValues(self.name, {
                        "state": switch,
                        "state_int": self._getForReporting()
                    }
            )
        else:
            logging.debug(
                "Receiver %s is in override mode, only rules with override can change it's state now" % self.name)

    def setOverrideMode(self, override):
        self.overrideMode = override
        if override:
            logging.warn("Receiver %s just went into override mode" % self.name)
        else:
            logging.warn("Receiver %s just went out of override mode" % self.name)

    def supported_states(self):
        return ["off", "on"]

    def current_state(self):
        return self.state

    def _getForReporting(self):
        if (not self.any_state):
            value = -1
            if self.state:
                value = self.supported_states().index(self.current_state())
            return value
        return -1

    def _setState(self, verb, state):
        None
