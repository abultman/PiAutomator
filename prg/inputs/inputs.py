import logging


class AnInput(object):
    def __init__(self, name, context, settings):
        """
        @type context: context.AutomationContext
        """
        self.context = context
        self.name = name
        self.settings = settings

    def publish(self, value):
        self.context.publishInputValues(self.name, value)

    def get(self, name=None):
        self.context.get
        if self.value:
            if name != None and isinstance(self.value, dict):
                return self.value[name]
            else:
                return self.value
        return None

class PollingInput(AnInput):
    def __init__(self, name, settings, g):
        super(PollingInput, self).__init__(name, settings, g)

    def refresh(self):
        logging.debug("refreshing %s" % self.name)
        value = self._read()
        if value:
            self.publish(value)
            logging.info("refreshed %s: %s" % (self.name, value))

    def _read(self):
        return None

