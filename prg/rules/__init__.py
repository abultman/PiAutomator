import schedule
from RuleParser import *
from rules import *

def init(config, inputs, receivers):
  parser = RuleParser()
  context = RuleContext(inputs, receivers)
  [context.add_rule(parser.parse(rule, context)) for rule in config.rules()]
  # topLevelRules = MatchingRules(_rules, inputs, receivers)
  schedule.every(5).seconds.do(context.checkrules)
  return context

