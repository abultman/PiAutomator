from RuleParser import *
from rules import *


def init(automation_context):
    parser = RuleParser()
    rule_context = RuleContext(automation_context)
    [rule_context.add_rule(parser.parse(rule, rule_context)) for rule in automation_context.config.rules()]
    return rule_context

