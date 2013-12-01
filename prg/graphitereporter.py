from graphitesend import GraphiteClient
import sys

class GraphiteReporter(object):
  def __init__(self, config, type = 'measurements'):
    self.g = None
    self.type = type
    self.config = config

  def __getG(self):
    if not self.g:
      try: 
        self.g = GraphiteClient(prefix='home', group='%s.'%self.type, graphite_server=self.config.getSetting(['graphite','host']))
      except:
        e = sys.exc_info()
        print "Unable to establish Graphite connection"
        print e
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
        print "Error sending to graphite"

  def send(self, metric, value, timestamp=None):
    g = self.__getG()
    if g:
      try:
        g.send(metric, value, timestamp)
      except:
        self.__destroyG()
        print "Error sending to graphite"
