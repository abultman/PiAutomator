import logging

class Action(object):
    def __init__(self, data):
        self.receiver = data['receiver']
        self.state = data['state']
        self.verb = data['verb']
        self.data = data

    def perform(self, rule_context, rule_state, override=False, overrideOff=False):
        """
        @type rule_context: rules.RuleContext
        """
        try:
            receiver = rule_context.automation_context.receivers[self.receiver]
            if overrideOff:
                receiver.setOverrideMode(False)
            elif override:
                receiver.setOverrideMode(True)
            receiver.do(self.verb, self.state, override)
        except:
            logging.warning("Receiver with name '%s' is unknown, skipping this action" % self.receiver)

    def __str__(self):
        return "%s" % self.data
