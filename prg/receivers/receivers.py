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
      logging.debug("Receiver %s is in override mode, only rules with override can change it's state now" % self.name)

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

  def _sendForReporting(self):
    value = -1
    if self.state:
      value = self.supported_states().index(self.current_state())
    self.g.send(self.name, value)

  def _setState(self, state):
    None