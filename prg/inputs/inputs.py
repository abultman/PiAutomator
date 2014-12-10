import logging


class AnInput(object):
    def __init__(self, name, context, settings):
        """
        @type context: context.AutomationContext
        @type settings: config.LocalSettings
        """
        self.context = context
        self.name = name
        self.settings = settings
        self.started = False

    def start(self):
        self.started = True

    def stop(self):
        self.started = False

    def publish(self, value, name = None):
        if not self.started: return

        if name is not None:
            # publish it under the specificed name (for 'all-inputs kind of setup')
            self.context.publishInputValues(name, value)
        else:
            # publish it under the name defined here
            self.context.publishInputValues(self.name, value)

class PollingInput(AnInput):
    def __init__(self, name, context, settings):
        super(PollingInput, self).__init__(name, context, settings)

    def refresh(self):
        logging.debug("refreshing %s" % self.name)
        value = self._read()
        if value:
            self.publish(value)
            logging.debug("refreshed %s: %s" % (self.name, value))

    def _read(self):
        return None

