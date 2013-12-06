import logging
from actions import *

_operators = {
  "less than": lambda x,y: int(x) < int(y),
  "greater than": lambda x,y: int(x) > int(y),
  "equal to": lambda x,y: str(x) == str(y)
}

class Rule(object):
  def __init__(self, rulename, data, inputs, receivers):
    self.actions = [Action(action) for action in data['actions']]
    self.receivers = receivers
    self.inputs = inputs
    self.override = "override" in data
    self.overrideOff = False
    if self.override and len(data["override"]) == 1:
      self.overrideOff = True
      logging.warn("rule '%s' has override configuration and will turn a possible override state off" % rulename)
    elif self.override:
      logging.warn("rule '%s' has override configuration and will turn a possible override state on" % rulename)

    self.rulename = rulename

  def matches(self):
    return False

  def performActions(self):
    [action.perform(self.receivers, self.override, self.overrideOff) for action in self.actions]

