import logging
import sys

from graphitesend import GraphiteClient


class GraphiteReporter(object):
    def __init__(self, config, type='piautomator'):
        self.g = None
        self.type = type
        self.config = config

    def __getG(self):
        def graphite_should_be_enabled():
            has_graphite = self.g
            graphite_enabled = self.config.get_setting(['graphite', 'enabled'], False)
            return not has_graphite and graphite_enabled

        if graphite_should_be_enabled():
            try:
                self.g = GraphiteClient(prefix='', group='%s.' % self.type,
                                        graphite_server=self.config.get_setting(['graphite', 'host']))
            except:
                e = sys.exc_info()
                logging.error("Unable to establish Graphite connection")
                self.g = None
        return self.g

    def __destroyG(self):
        if self.g:
            try:
                self.g.disconnect()
            except:
                None

        self.g = None

    def send_dict(self, data, timestamp=None):
        g = self.__getG()
        if g:
            try:
                g.send_dict(data, timestamp)
            except:
                self.__destroyG()
                logging.error("Error sending to graphite")

    def send(self, metric, value, timestamp=None):
        g = self.__getG()
        if g:
            try:
                g.send(metric, value, timestamp)
            except:
                self.__destroyG()
                logging.error("Error sending to graphite")
