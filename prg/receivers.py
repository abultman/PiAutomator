import subprocess, logging, threading, Queue
import schedule
from graphitereporter import GraphiteReporter

jobqueue = Queue.Queue()

class StateError(Exception):
    pass


class Receiver(object):
  def __init__(self, name, config, settings, g):
    self.settings = settings
    self.name = name
    self.config = config
    self.state = None
    self.state = g

  def do(self, switch):
    if (switch not in self.supported_states()):
      raise StateError("Illegal state passed to set. %s not in %s" %(switch, self.supported_states()))

    if self.state != switch or self.state == None:
      self.setState(switch)
      logging.warn("Turned %s %s" % (self.name, switch))
    self.state = switch

  def supported_states(self):
    return ["off", "on"]

  def current_state(self):
    return self.state

  def _sendForReporting(self, g):
    value = self.supported_states().index(self.current_state())
    g.send(self.name, value)

  def _setState(self, state):
    None

class ToolCommandReceiver(Receiver):
  def __init__(self, name, config, settings):
    super(ToolCommandReceiver, self).__init__(name, config, settings)

  def _setState(self, state):
    command = "%s/tools/%s" % (self.config.get_basedir(), self.settings['type'])
    args = "%s %s" % (self.settings['command'], state)
    toexec = "%s %s" % (command, args)
    jobqueue.put(toexec)

def init(config):
  g = GraphiteReporter(type = "receivers")
  global _receivers
  _receivers = {}
  receivers = config.receivers()
  for name in receivers:
    _receivers[name] = eval("%s(name, config, receivers[name], g)" % receivers[name]['type'])

  worker_thread = threading.Thread(target=__worker_main__)
  worker_thread.daemon = True
  worker_thread.start()

  schedule.every(10).seconds.do(__graphiteReporter__)

  return _receivers

def __graphiteReporter__():
  for receiver in _receivers:
    receiver._sendForReporting()


def __worker_main__():
  while True:
    toexec = jobqueue.get()
    logging.warn(toexec)
    subprocess.call(toexec, shell=True)

def receiver(name):
  return _receivers[name]
