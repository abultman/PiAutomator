import logging
from pyparsing import *
from rules import _operators
from conditional import *
from schedulerule import *

_known_rules = {
  'input-rule': ConditionalRule,
  'schedule-rule': ScheduleRule
}


class RuleParser(object):


  def __init__(self):
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
    word = Word(alphas + nums)
    ignoredWord = Suppress(word)
    verb = ignoredWord
    number = Word(nums)


    word_or_sentence = (word | quotedString.setParseAction(removeQuotes))

    def __actions():
      state = word_or_sentence.setResultsName("state")
      receiver = word.setResultsName("receiver")

      action = Group(verb + receiver + state)
      return Group(OneOrMore(action + Optional(_and))).setResultsName("actions")
    actions = __actions()


    def receiver_input_rule():
      sensor = word.setResultsName("sensor")
      metric = word.setResultsName("metric")
      sensormetric = sensor + dot + metric

      operator = oneOf(_operators.keys()).setResultsName("operator")
      value = word_or_sentence.setResultsName("value")
      comparison = operator + value

      condition = Group(sensormetric + _is + comparison)
      conditions = Group(OneOrMore(condition + Optional(_and))).setResultsName("conditions")

      return when + conditions + then + actions

    def schedule_rule():
      timeIndication = at + Combine(number + Optional(colon + number)).setResultsName("time")

      recurring2 = Group(every + number.setResultsName("count") + oneOf("days hours seconds weeks").setResultsName("unit") + Optional(timeIndication)).setResultsName("pluralSchedule")
      recurring1 = Group(every + oneOf("day hour second week").setResultsName("unit") + Optional(timeIndication)).setResultsName("singularSchedule")

      return (recurring1 | recurring2) + actions + Optional(override + Optional("off")).setResultsName("override")

    self.rule = (receiver_input_rule().setResultsName("input-rule") | schedule_rule().setResultsName("schedule-rule")) + stringEnd


  def rawParse(self, toParse):
    return self.rule.parseString(toParse)

  def parse(self, toParse, inputs, receivers):
    self.logger.warn(toParse)
    raw_parse = self.rawParse(toParse)
    rule_type = raw_parse.getName()
    my_class = _known_rules[rule_type]
    return my_class(toParse, raw_parse[rule_type], inputs, receivers)