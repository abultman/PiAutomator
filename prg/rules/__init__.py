from RuleParser import *
from rules import *


def init(context):
    parser = RuleParser()
    rule_context = RuleContext(context)
    [rule_context.add_rule(parser.parse(rule, rule_context)) for rule in context.config.rules()]
    return rule_context

