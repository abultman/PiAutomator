import logging
from pyparsing import *
from rules import operators
from conditional import *
from rules import RuleState
from schedulerule import *

_known_rules = {
  'input-rule': ConditionalRule,
  'schedule-rule': ScheduleRule
}


class RuleParser(object):

  def __init__(self):
    self.rules_parsed = 0
    self.logger = logging.getLogger("rule-parser")
    self.logger.setLevel(logging.INFO)
    dot = Suppress(".")
    colon = Word(":")
    _is = Suppress("is")
    _and = Suppress("and")
    then = Suppress("then")
    when = Suppress("when")
    override = Suppress("override")
    every = Suppress("every")
    at = Suppress("at")
    word = Word(alphas + nums + "-" + "_")
    ignoredWord = Suppress(word)
    verb = word.setResultsName('verb')
    number = Word(nums)
    word_or_sentence = (word | quotedString.setParseAction(removeQuotes))

    identified_by = Suppress("identified by")

    def __actions():
      state = word_or_sentence.setResultsName("state")
      receiver = word.setResultsName("receiver")

      action = Group(verb + receiver + state)
      actions = ZeroOrMore(action + _and) + action
      return Group(actions).setResultsName("actions")
    actions = __actions()


    def receiver_input_rule():
      sensor = word.setResultsName("sensor")
      metric = word.setResultsName("metric")
      sensormetric = sensor + dot + metric

      operator = oneOf(operators.keys()).setResultsName("operator")
      value = word_or_sentence.setResultsName("value")
      comparison = operator + value

      condition = Group(sensormetric + _is + comparison)
      res = ZeroOrMore(condition + _and) + condition
      conditions = Group(res).setResultsName("conditions")

      return when + conditions + then + actions

    def schedule_rule():
      timeIndication = at + Combine(number + Optional(colon + number)).setResultsName("time")

      recurring2 = Group(every + number.setResultsName("count") + oneOf("days hours seconds weeks").setResultsName("unit") + Optional(timeIndication)).setResultsName("pluralSchedule")
      recurring1 = Group(every + oneOf("day hour second week").setResultsName("unit") + Optional(timeIndication)).setResultsName("singularSchedule")

      return (recurring1 | recurring2) + actions + Optional(override + Optional("off")).setResultsName("override")

    rule_type = (
                  receiver_input_rule().setResultsName("input-rule") |
                  schedule_rule().setResultsName("schedule-rule")
                )

    self.rule = rule_type + Optional(identified_by + word.setResultsName("rule-id"))

  def rawParse(self, toParse):
    """
    @rtype: matplotlib.pyparsing.ParseResults
    """
    self.rules_parsed = self.rules_parsed + 1
    return self.rule.parseString(toParse, parseAll=True)

  def parse(self, toParse, context):
    """
    @rtype: rules.Rule
    """
    raw_parse = self.rawParse(toParse)
    rule_id = raw_parse.get('rule-id', 'rule-%d' % self.rules_parsed)
    rule_type = raw_parse.getName()
    my_class = _known_rules[rule_type]
    rule_state = RuleState(rule_id, toParse)
    return my_class(context, rule_state, raw_parse[rule_type])