import schedule
from RuleParser import *

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