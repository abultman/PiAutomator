import dhtreader, threading, Queue, schedule, logging
from timeout import timeout, TimeoutError
from config import AutomationConfig
from graphitereporter import GraphiteReporter

class AnInput(object):
  def __init__(self, name, settings, g):
    self.settings = settings
    self.g = g
    self.name = name

  def refresh(self):
    logging.debug("refreshing %s" % self.name)
    self.value = self._read()
    if self.value:
      logging.info("refreshed %s: %s" % (self.name, self.value))
      if isinstance(self.value, dict):
        for key in self.value:
          self.g.send('%s.%s' % (self.name, key), self.value[key])
      else:
        self.g.send('%s' % (self.name), self.value)

  def _read(self):
    return None

  def get(self, name=None):
    if self.value:
      if name != None and isinstance(self.value, dict):
        return self.value[name]
      else:
        return self.value
    return None

global dhtinited
dhtinited = False

class DHT22(AnInput):
  def __init__(self, name, settings, g):
    super(DHT22, self).__init__(name, settings, g)
    self.settings = settings
    self.g = g
    global dhtinited
    if not dhtinited:
      dhtreader.init()
      global dhtinited
      dhtinited = True

  def _read(self):
    try:
      value = dhtreader.read(22, self.settings['pin'])
      if value:
        return {"temperature": value[0], "humidity": value[1]}
    except TimeoutError:
      return None
    return None

 
jobqueue = Queue.Queue()
    
def __worker_main__():
  while True:
    jobqueue.get()()

def init(config):
  g = GraphiteReporter(config)
  global _inputs
  _inputs = {}
  inputs = config.inputs()
  for name in inputs:
    _inputs[name] = eval("%s(name, inputs[name], g)" % inputs[name]['type'])
    _inputs[name].refresh()
    schedule.every(10).seconds.do(jobqueue.put, _inputs[name].refresh)

  worker_thread = threading.Thread(target=__worker_main__)
  worker_thread.daemon = True
  worker_thread.start()

  return _inputs
