from RuleParser import *
from rules import *


def init(config, inputs, receivers):
    parser = RuleParser()
    context = RuleContext(inputs, receivers)
    [context.add_rule(parser.parse(rule, context)) for rule in config.rules()]
    context.start()
    return context

