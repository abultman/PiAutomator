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
    self.g = g
    self.overrideMode = False

  def do(self, switch, override = False):
    if (switch not in self.supported_states()):
      raise StateError("Illegal state passed to set. %s not in %s" %(switch, self.supported_states()))

    if override or not self.overrideMode:
      if self.state != switch or self.state == None:
        self._setState(switch)
        logging.warn("Turned %s %s" % (self.name, switch))
      self.state = switch
    else:
      logging.warn("Receiver %s is in override mode, only rules with override can change it's state now" % self.name)

  def supported_states(self):
    return ["off", "on"]

  def current_state(self):
    return self.state

  def _sendForReporting(self):
    value = -1
    if self.state:
      value = self.supported_states().index(self.current_state())
    self.g.send(self.name, value)

  def _setState(self, state):
    None

class ToolCommandReceiver(Receiver):
  def __init__(self, name, config, settings, g):
    super(ToolCommandReceiver, self).__init__(name, config, settings, g)

  def _setState(self, state):
    command = "%s/tools/%s" % (self.config.get_basedir(), self.settings['command'])
    args = "%s %s" % (self.settings['args'], state)
    toexec = "%s %s" % (command, args)
    jobqueue.put(toexec)

def init(config):
  g = GraphiteReporter(config, "receivers")
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
    _receivers[receiver]._sendForReporting()


def __worker_main__():
  while True:
    toexec = jobqueue.get()
    logging.warn(toexec)
    subprocess.call(toexec, shell=True)

def receiver(name):
  return _receivers[name]
