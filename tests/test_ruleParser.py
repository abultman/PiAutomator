from unittest import TestCase
from rules import RuleParser, operators
from rules.conditional import ConditionalRule
from rules.rules import RuleContext
from rules.schedulerule import ScheduleRule
from mock import Mock, MagicMock


class TestRuleParser(TestCase):
    def setUp(self):
        mock = Mock()
        mock.getRuleValue = MagicMock(return_value = None)
        self.parser = RuleParser()
        self.context = RuleContext(mock)

    def test_parse_simple_conditional(self):
        parse = self.parser.parse("when input.metric is less than 10 then turn heat up", self.context)
        self.assertIsInstance(parse, ConditionalRule)
        self.assertEqual(parse.always_fire, False)

    def test_parse_simple_conditional_identified_by(self):
        parse = self.parser.parse("when input.metric is less than 10 then turn heat up identified by my_name1-awesome",
                                  self.context)
        self.assertEqual(parse.rule_state.rule_id, "my_name1-awesome")

    def test_parse_mulitple_conditional_identified_by(self):
        parse = self.parser.parse(
            "when input.metric is less than 10 and input3.othermetric.that.is.super.nested is equal to 43 then turn heat up",
            self.context)
        self.assertIsInstance(parse, ConditionalRule)
        self.assertEqual(len(parse.conditions), 2)
        self.assertEqual(parse.conditions[0].input, 'input.metric')
        self.assertEqual(parse.conditions[0].operator, operators['less than'])
        self.assertEqual(parse.conditions[0].temporal, 'is')

        self.assertEqual(parse.conditions[1].input, 'input3.othermetric.that.is.super.nested')
        self.assertEqual(parse.conditions[1].operator, operators['equal to'])

        self.assertEqual(len(parse.actions), 1)
        self.assertEqual(parse.actions[0].receiver, 'heat')
        self.assertEqual(parse.actions[0].state, 'up')

    def test_parse_mulitple_action_identified_by(self):
        parse = self.parser.parse(
            "when input.metric is less than 10 and input3.othermetric is equal to 43 then turn heat up and send echo 2",
            self.context)
        self.assertIsInstance(parse, ConditionalRule)
        self.assertEqual(len(parse.conditions), 2)

        self.assertEqual(len(parse.actions), 2)
        self.assertEqual(parse.actions[0].always_fire, False)
        self.assertEqual(parse.actions[0].receiver, 'heat')
        self.assertEqual(parse.actions[0].state, 'up')
        self.assertEqual(parse.actions[0].verb, 'turn')
        self.assertEqual(parse.actions[1].always_fire, False)
        self.assertEqual(parse.actions[1].receiver, 'echo')
        self.assertEqual(parse.actions[1].state, '2')

    def test_scheduled_rule(self):
        parse = self.parser.parse("every day turn heat up", self.context)
        self.assertIsInstance(parse, ScheduleRule)

        self.assertEqual("schedule.every(1).day", parse.scheduleStr[0])

    def test_scheduled_rule_with_time(self):
        parse = self.parser.parse("every day at 10:40 turn heat up", self.context)
        self.assertIsInstance(parse, ScheduleRule)

        self.assertEqual(parse.scheduleStr[0], "schedule.every(1).day.at('10:40')")

    def test_scheduled_rule_with_time_hour(self):
        parse = self.parser.parse("every hour at :30 turn homefan on", self.context)
        self.assertIsInstance(parse, ScheduleRule)
        self.assertEqual(parse.scheduleStr[0], "schedule.every(1).hour.at(':30')")

    def test_scheduled_rule_with_time_hour2(self):
        parse = self.parser.parse("every 5 hours at :30 turn heat up", self.context)
        self.assertIsInstance(parse, ScheduleRule)
        self.assertEqual(parse.scheduleStr[0], "schedule.every(5).hours.at(':30')")

    def test_day_of_week(self):
        parse = self.parser.parse("every monday turn heat up", self.context)
        self.assertIsInstance(parse, ScheduleRule)
        self.assertEqual(parse.scheduleStr[0], "schedule.every(1).monday")

    def test_day_of_week_with_time(self):
        parse = self.parser.parse("every sunday at 12:30 turn heat up", self.context)
        self.assertIsInstance(parse, ScheduleRule)
        self.assertEqual(parse.scheduleStr[0], "schedule.every(1).sunday.at('12:30')")

    def test_every_weekday(self):
        parse = self.parser.parse("every weekday at 12:30 turn heat up", self.context)
        self.assertIsInstance(parse, ScheduleRule)
        self.assertEqual(len(parse.scheduleStr), 5)
        self.assertEqual(parse.scheduleStr[0], "schedule.every(1).monday.at('12:30')")
        self.assertEqual(parse.scheduleStr[1], "schedule.every(1).tuesday.at('12:30')")
        self.assertEqual(parse.scheduleStr[2], "schedule.every(1).wednesday.at('12:30')")
        self.assertEqual(parse.scheduleStr[3], "schedule.every(1).thursday.at('12:30')")
        self.assertEqual(parse.scheduleStr[4], "schedule.every(1).friday.at('12:30')")

    def test_every_weekendday(self):
        parse = self.parser.parse("every weekendday at 12:30 turn heat up", self.context)
        self.assertIsInstance(parse, ScheduleRule)
        self.assertEqual(len(parse.scheduleStr), 2)
        self.assertEqual(parse.scheduleStr[0], "schedule.every(1).saturday.at('12:30')")
        self.assertEqual(parse.scheduleStr[1], "schedule.every(1).sunday.at('12:30')")

    def test_multiple_days(self):
        parse = self.parser.parse("every monday and thursday and sunday at 12:30 turn heat up", self.context)
        self.assertIsInstance(parse, ScheduleRule)
        self.assertEqual(len(parse.scheduleStr), 3)
        self.assertEqual(parse.scheduleStr[0], "schedule.every(1).monday.at('12:30')")
        self.assertEqual(parse.scheduleStr[1], "schedule.every(1).thursday.at('12:30')")
        self.assertEqual(parse.scheduleStr[2], "schedule.every(1).sunday.at('12:30')")

    def test_allows_always_prefix(self):
        parse = self.parser.parse("always when my.input is equal to on then turn receiver on", self.context)
        self.assertIsInstance(parse, ConditionalRule)
        self.assertEqual(parse.always_fire, True)

    def test_actions_allow_always_too(self):
        parse = self.parser.parse("always when my.input is equal to on then always turn receiver on", self.context)
        self.assertIsInstance(parse, ConditionalRule)
        self.assertEqual(parse.always_fire, True)
        self.assertEqual(parse.actions[0].always_fire, True)

    def test_can_nest_conditional_in_schedule(self):
        parse = self.parser.parse("every 10 minutes when lightlevel.level is greater than 10 then turn lights off", self.context)
        self.assertIsInstance(parse, ScheduleRule)
        self.assertIsInstance(parse.nested_rule, ConditionalRule)
        self.assertEqual(parse.nested_rule.actions[0].always_fire, False)
        self.assertEqual(parse.nested_rule.actions[0].receiver, 'lights')
        self.assertEqual(parse.nested_rule.actions[0].state, 'off')
        self.assertEqual(parse.nested_rule.actions[0].verb, 'turn')

    def test_can_be_was_too(self):
        parse = self.parser.parse("when my.input was less than 10 then send notification turbo", self.context)
        self.assertIsInstance(parse, ConditionalRule)
        self.assertEqual(parse.conditions[0].temporal, 'was')