import logging
import schedule
from actions import *

operators = {
  "less than": lambda x,y: int(x) < int(y),
  "greater than": lambda x,y: int(x) > int(y),
  "equal to": lambda x,y: str(x) == str(y)
}

class RuleState(object):
  def __init__(self, rule_id, rule_name):
    self.data = {
      "total_fired_count" : 0,
      "total_success_count" : 0,
      "total_failed_count" : 0,
      "consecutive_success_count" : 0,
      "consecutive_failed_count" : 0
    }
    self.rule_id = rule_id
    self.rule_name = rule_name

  def success(self):
    self.incr("total_fired_count")
    self.incr("total_success_count")
    self.incr("consecutive_success_count")
    self.reset("consecutive_failed_count")

  def failed(self):
    self.incr("total_fired_count")
    self.incr("total_failed_count")
    self.incr("consecutive_failed_count")
    self.reset("consecutive_success_count")

  def reset(self, name):
    self.data[name] = 0

  def incr(self, name):
    if name in self.data:
      self.data[name] = self.data[name] + 1
    else:
      self.data[name] = 1

class Rule(object):
  def __init__(self, rule_context, rule_state, data):
    """
    @type rule_state: RuleState
    @type rule_context: RuleContext
    @type data: matplotlib.pyparsing.ParseResults
    """
    self.actions = [Action(action) for action in data['actions']]
    self.override = "override" in data
    self.overrideOff = False
    if self.override and len(data["override"]) == 1:
      self.overrideOff = True
      logging.warn("rule '%s' has override configuration and will turn a possible override state off" % rule_state.rule_name)
    elif self.override:
      logging.warn("rule '%s' has override configuration and will turn a possible override state on" % rule_state.rule_name)
    self.rule_state = rule_state
    self.rule_context = rule_context

  def matches(self):
    return False

  def performActions(self):
    [action.perform(self.rule_context, self.rule_state, self.override, self.overrideOff) for action in self.actions]

  def start(self):
    pass

  def stop(self):
    pass

class RuleContext(object):
  def __init__(self, inputs, receivers):
    self.inputs = inputs
    self.receivers = receivers
    self.rules = {}
    self.started = False

  def add_rule(self, rule):
    """
    @type rule: rules.Rule
    """
    self.rules[rule.rule_state.rule_id] = rule
    if self.started:
      rule.start()

  def start(self):
    self.started = True
    [rule.start() for rule in self.rules.values()]
    self.schedule = schedule.every(5).seconds.do(self.checkrules)

  def stop(self):
    schedule.cancel_job(self.schedule)
    [rule.stop() for rule in self.rules.values()]

  def checkrules(self):
    self.findMatchingRules(self.inputs).andPerformTheirActions(self.receivers)

  def findMatchingRules(self, inputs):
    def rulesMatchingInputs():
      for rule in self.rules.values():
        if rule.matches(): yield rule

    return MatchingRules(rulesMatchingInputs(), self.inputs, self.receivers)

class MatchingRules(object):
  def __init__(self, matchingRules, inputs, receivers):
    self.matchingRules = matchingRules
    self.receivers = receivers
    self.inputs = inputs

  def andPerformTheirActions(self, receivers):
    for rule in self.matchingRules:
      rule.performActions()



