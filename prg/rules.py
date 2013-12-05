import logging
from pyparsing import *
import schedule

_operators = {
  "less than": lambda x,y: int(x) < int(y),
  "greater than": lambda x,y: int(x) > int(y),
  "equal to": lambda x,y: str(x) == str(y)
}

class Action(object):
  def __init__(self, data):
    self.receiver = data['receiver']
    self.state = data['state']
    self.data = data

  def perform(self, receivers, override = False, overrideOff = False):
    receiver = receivers[self.receiver]
    if overrideOff:
      receiver.setOverrideMode(False)
    elif override:
      receiver.setOverrideMode(True)
    receiver.do(self.state, override)
  
  def __str__(self):
    return "%s" % self.data

class Condition(object):
  def __init__(self, data):
    self.data = data
    self.sensor = data['sensor']
    self.metric = data['metric']
    self.operator = _operators[self.data['operator']]
    self.value = self.data['value']

  def matches(self, inputs):
    sensor = inputs[self.sensor]
    sensorValue = sensor.get(self.metric)
    if sensorValue:
      return self.operator(sensorValue, self.data['value'])
    else:
      return False

  def __str__(self):
    return "%s" % self.data

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
    all(action.perform(self.receivers, self.override, self.overrideOff) for action in self.actions)

class ConditionalRule(Rule):
  def __init__(self, rulename, data, inputs, receivers):
    super(ConditionalRule, self).__init__(rulename, data, inputs, receivers)
    self.conditions = [Condition(condition) for condition in data['conditions']]

  def matches(self):
    return all(condition.matches(self.inputs) for condition in self.conditions)

  def __str__(self):
    return "actions %s\nconditions %s" % (self.actions, self.conditions)

class ScheduleRule(Rule):
  def __init__(self, rulename, data, inputs, receivers):
    super(ScheduleRule, self).__init__(rulename, data, inputs, receivers)
    if "pluralSchedule" in data.keys():
      schedule_data = data['pluralSchedule']
      toeval = "schedule.every(%s).%s" % (schedule_data['count'], schedule_data['unit'])
      if "time" in schedule_data.keys():
        toeval = "%s.at('%s')" %(toeval, schedule_data["time"])
      eval(toeval).do(self.performActions)
    else:
      schedule_data = data['singularSchedule']
      toeval = "schedule.every().%s" % (schedule_data['unit'])
      if "time" in schedule_data.keys():
        toeval = "%s.at('%s')" %(toeval, schedule_data["time"])
      eval(toeval).do(self.performActions)

  def __str__(self):
    return "actions %s" % (self.actions)


class RuleParser(object):
  def __init__(self):
    dot = Suppress(".")
    colon = Word(":")
    _is = Suppress("is")
    _and = Suppress("and")
    then = Suppress("then")
    when = Suppress("when")
    override = Suppress("override")
    every = Suppress("every")
    at = Suppress("at")
    word = Word(alphas + nums)
    ignoredWord = Suppress(word)
    verb = ignoredWord
    number = Word(nums)

    def __actions():
      state = word.setResultsName("state")
      receiver = word.setResultsName("receiver")

      action = Group(verb + receiver + state)
      return Group(OneOrMore(action + Optional(_and))).setResultsName("actions")
    actions = __actions()


    def receiver_input_rule():
      sensor = word.setResultsName("sensor")
      metric = word.setResultsName("metric")
      sensormetric = sensor + dot + metric

      operator = oneOf(_operators.keys()).setResultsName("operator")
      value = (word | '".*"').setResultsName("value")
      comparison = operator + value

      condition = Group(sensormetric + _is + comparison)
      conditions = Group(OneOrMore(condition + Optional(_and))).setResultsName("conditions")

      return when + conditions + then + actions

    def schedule_rule():
      timeIndication = at + Combine(number + Optional(colon + number)).setResultsName("time")

      recurring2 = Group(every + number.setResultsName("count") + oneOf("days hours seconds weeks").setResultsName("unit") + Optional(timeIndication)).setResultsName("pluralSchedule")
      recurring1 = Group(every + oneOf("day hour second week").setResultsName("unit") + Optional(timeIndication)).setResultsName("singularSchedule")

      return (recurring1 | recurring2) + actions + Optional(override + Optional("off")).setResultsName("override")

    self.rule = receiver_input_rule() | schedule_rule()


  def rawParse(self, toParse):
    return self.rule.parseString(toParse)

  def parse(self, toParse, inputs, receivers):
    raw_parse = self.rawParse(toParse)
    if "conditions" in raw_parse.keys():
      return ConditionalRule(toParse, raw_parse, inputs, receivers)
    else:
      return ScheduleRule(toParse, raw_parse, inputs, receivers)

def init(config, inputs, receivers):
  parser = RuleParser()
  global _rules
  _rules = [parser.parse(rule, inputs, receivers) for rule in config.rules()]
  topLevelRules = MatchingRules(_rules, inputs, receivers)
  schedule.every(5).seconds.do(topLevelRules.checkrules)
  return MatchingRules(_rules, inputs, receivers)

class MatchingRules(object):
  def __init__(self, matchingRules, inputs, receivers):
    self.matchingRules = matchingRules
    self.receivers = receivers
    self.inputs = inputs

  def checkrules(self):
    self.findMatchingRules(self.inputs).andPerformTheirActions(self.receivers)

  def andPerformTheirActions(self, receivers):
    for rule in self.matchingRules:
      rule.performActions()

  def findMatchingRules(self, inputs):
    def rulesMatchingInputs():
      for rule in _rules:
        if rule.matches(): yield rule

    return MatchingRules(rulesMatchingInputs(), self.inputs, self.receivers)
