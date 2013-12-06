import Queue
import threading
import logging
import subprocess

import schedule

from graphitereporter import *


__myclasses__ = {}

__logger__ = logging.getLogger("recievers")
__logger__.setLevel(logging.INFO)

def __load_receiver__(elem, config):
  if elem not in __myclasses__:
    __logger__.info("Loading receiver of type %s" % elem)
    mod = __import__(elem, globals = globals())
    __myclasses__[elem] = getattr(mod, elem)
    if hasattr(mod, 'init'):
      getattr(mod, 'init')(config)
      __logger__.info("Initializing %s" % elem)

  return __myclasses__[elem]

__author__ = 'administrator'

def init(config):
  g = GraphiteReporter(config, "receivers")
  global _receivers
  _receivers = {}
  receivers = config.receivers()
  for name in receivers:
    my_class = __load_receiver__(receivers[name]['type'], config)
    _receivers[name] = my_class(name, config, receivers[name], g)

  schedule.every(10).seconds.do(__graphiteReporter__)

  return _receivers

def __graphiteReporter__():
  for receiver in _receivers:
    _receivers[receiver]._sendForReporting()


def receiver(name):
  return _receivers[name]
