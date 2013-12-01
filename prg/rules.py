#!/usr/bin/python
from pyparsing import *
from config import *

_operators = {
  "less than": lambda x,y: int(x) < int(y),
  "greater than": lambda x,y: int(x) > int(y)
}

class Action(object):
  def __init__(self, data):
    self.data = data

  def perform(self, receivers):
    receiver = receivers[self.data['receiver']]
    receiver.do(self.data['state'])
  
  def __str__(self):
    return "%s" % data

class Condition(object):
  def __init__(self, data):
    self.data = data

  def matches(self, inputs):
    sensor = inputs[self.data['sensor']]
    sensorValue = sensor.get(self.data['metric'])
    if sensorValue:
      aoperator = _operators[self.data['operator']]
      return aoperator(sensorValue, self.data['value'])
    else:
      return False
      

  def __str__(self):
    return "%s" % data

class Rule(object):
  def __init__(self, data):
    self.conditions = [Condition(condition) for condition in data['conditions']]
    self.actions = [Action(action) for action in data['actions']]

  def matches(self, inputs):
    return all(condition.matches(inputs) for condition in self.conditions)

  def performActions(self, receivers):
    all(action.perform(receivers) for action in self.actions)

  def __str__(self):
    return "actions %s\nconditions %s" % (self.actions, self.conditions)

class RuleParser(object):
  def __init__(self):
    dot = Suppress(".")
    _is = Suppress("is")
    _and = Suppress("and")
    then = Suppress("then")
    turn = Suppress("turn")
    when = Suppress("when")
    word = Word(alphas + nums)
    number = Word(nums)
    
    sensor = word.setResultsName("sensor")
    metric = word.setResultsName("metric")
    sensormetric = sensor + dot + metric

    operator = oneOf(["greater than", "less than"]).setResultsName("operator")
    value = number.setResultsName("value")
    comparison = operator + value

    condition = Group(sensormetric + _is + comparison)
    conditions = Group(OneOrMore(condition + Optional(_and))).setResultsName("conditions")

    state = oneOf("on off").setResultsName("state")
    receiver = word.setResultsName("receiver")

    action = Group(turn + receiver + state)
    actions = Group(OneOrMore(action + Optional(_and))).setResultsName("actions")

    self.rule = when + conditions + then + actions + StringEnd()

  def parse(self, toParse):
    return Rule(self.rule.parseString(toParse))

def init(config):
  parser = RuleParser()
  global _rules
  _rules = [parser.parse(rule) for rule in config.rules()]
  return MatchingRules(_rules)

class MatchingRules(object):
  def __init__(self, matchingRules):
    self.matchingRules = matchingRules

  def andPerformTheirActions(self, receivers):
    for rule in self.matchingRules:
      rule.performActions(receivers)

  def findMatchingRules(self, inputs):
    def rulesMatchingInputs():
      for rule in _rules:
        if rule.matches(inputs): yield rule

    return MatchingRules(rulesMatchingInputs())

