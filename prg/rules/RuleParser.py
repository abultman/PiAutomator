import hashlib
import logging
from pyparsing import Suppress, Word, alphas, nums, quotedString, removeQuotes, Group, ZeroOrMore, oneOf, Combine, Optional, ParseException
from rules import RuleState, operators
from conditional import ConditionalRule
from schedulerule import ScheduleRule

_known_rules = {
    'input-rule': ConditionalRule,
    'nested-input-rule': ConditionalRule,
    'schedule-rule': ScheduleRule
}

__logger__ = logging.getLogger('rule-parser')
__logger__.setLevel(logging.INFO)

class RuleParser(object):
    def __init__(self):
        self.rules_parsed = 0
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
            return Optional("always").setResultsName("always_fire_actions") + Group(actions).setResultsName("actions") + Optional(override + Optional("off")).setResultsName("override")

        actions = __actions()


        def receiver_input_rule():
            input = Combine(ZeroOrMore(word + ".") + word).setResultsName("input")

            operator = oneOf(operators.keys()).setResultsName("operator")
            value = word_or_sentence.setResultsName("value")
            comparison = operator + value

            is_or_was = Word("is") | Word("was")

            condition = Group(input + is_or_was.setResultsName("temporal") + comparison)
            res = ZeroOrMore(condition + _and) + condition
            conditions = Group(res).setResultsName("conditions")

            return Optional("always").setResultsName("always_fire_rule") + when + conditions + then + actions

        def schedule_rule():
            timeIndication = at + Combine(Optional(number) + colon + number).setResultsName("time")

            recurringPlural = Group(
                every + number.setResultsName("count") + oneOf("days hours minutes seconds weeks").setResultsName(
                    "unit") + Optional(timeIndication)).setResultsName("pluralSchedule")

            recurringSingular = Group(
                every + oneOf("day hour minute second week sunday weekday weekendday").setResultsName("unit") + Optional(timeIndication)).setResultsName(
                "singularSchedule")

            dayOfWeek = oneOf("monday tuesday wednesday thursday friday saturday sunday")
            recurringDay = Group(
                every + Group(ZeroOrMore(dayOfWeek + _and) + dayOfWeek).setResultsName("unit") + Optional(timeIndication)).setResultsName(
                "singularSchedule")

            return (recurringPlural | recurringSingular |recurringDay) + (actions | receiver_input_rule().setResultsName("nested-input-rule"))

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
        try :
            return self.rule.parseString(toParse, parseAll=True)
        except ParseException as e:
            __logger__.error("Error parsing rule %s", toParse)
            __logger__.exception(e)
            raise e

    def __build_rule__(self, raw_parse, rule_context, rule_id, rule_type, toParse, nested_rule = None):
        my_class = _known_rules[rule_type]
        rule_state = RuleState(rule_id, toParse, rule_context)
        return my_class(rule_context, rule_state, raw_parse[rule_type], nested_rule)

    def parse(self, toParse, rule_context):
        """
        @rtype: rules.Rule
        """
        raw_parse = self.rawParse(toParse)

        rule_id = raw_parse.get('rule-id', 'rule-%s' % hashlib.md5(toParse).hexdigest())
        rule_type = raw_parse.getName()

        nested_rule = None
        for key in raw_parse.keys():
            if key.startswith('nested-'):
                nested_rule = self.__build_rule__(raw_parse, rule_context, rule_id + "_1", key, toParse)

        return self.__build_rule__(raw_parse, rule_context, rule_id, rule_type, toParse, nested_rule)

