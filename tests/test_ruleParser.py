from unittest import TestCase
from rules import RuleParser, operators
from rules.conditional import ConditionalRule
from rules.rules import RuleContext
from rules.schedulerule import ScheduleRule


class TestRuleParser(TestCase):

  def setUp(self):
    self.parser = RuleParser()
    self.context = RuleContext({})

  def test_parse_simple_conditional(self):
    parse = self.parser.parse("when input.metric is less than 10 then turn heat up", self.context)
    self.assertIsInstance(parse, ConditionalRule)

  def test_parse_simple_conditional_identified_by(self):
    parse = self.parser.parse("when input.metric is less than 10 then turn heat up identified by my_name1-awesome", self.context)
    self.assertEqual(parse.rule_state.rule_id, "my_name1-awesome")

  def test_parse_mulitple_conditional_identified_by(self):
    parse = self.parser.parse("when input.metric is less than 10 and input3.othermetric.that.is.super.nested is equal to 43 then turn heat up", self.context)
    self.assertIsInstance(parse, ConditionalRule)
    self.assertEqual(len(parse.conditions), 2)
    self.assertEqual(parse.conditions[0].input, 'input.metric')
    self.assertEqual(parse.conditions[0].operator, operators['less than'])

    self.assertEqual(parse.conditions[1].input, 'input3.othermetric.that.is.super.nested')
    self.assertEqual(parse.conditions[1].operator, operators['equal to'])

    self.assertEqual(len(parse.actions), 1)
    self.assertEqual(parse.actions[0].receiver, 'heat')
    self.assertEqual(parse.actions[0].state, 'up')

  def test_parse_mulitple_action_identified_by(self):
    parse = self.parser.parse("when input.metric is less than 10 and input3.othermetric is equal to 43 then turn heat up and send echo 2", self.context)
    self.assertIsInstance(parse, ConditionalRule)
    self.assertEqual(len(parse.conditions), 2)

    self.assertEqual(len(parse.actions), 2)
    self.assertEqual(parse.actions[0].receiver, 'heat')
    self.assertEqual(parse.actions[0].state, 'up')
    self.assertEqual(parse.actions[0].verb, 'turn')
    self.assertEqual(parse.actions[1].receiver, 'echo')
    self.assertEqual(parse.actions[1].state, '2')

  def test_scheduled_rule(self):
    parse = self.parser.parse("every day turn heat up", self.context)
    self.assertIsInstance(parse, ScheduleRule)

    self.assertEqual(parse.scheduleStr, "schedule.every().day")

  def test_scheduled_rule_with_time(self):
    parse = self.parser.parse("every day at 10:40 turn heat up", self.context)
    self.assertIsInstance(parse, ScheduleRule)

    self.assertEqual(parse.scheduleStr, "schedule.every().day.at('10:40')")

  def test_scheduled_rule_with_time_hour(self):
    parse = self.parser.parse("every hour at 30 turn heat up", self.context)
    self.assertIsInstance(parse, ScheduleRule)
    self.assertEqual(parse.scheduleStr, "schedule.every().hour.at('30')")

  def test_scheduled_rule_with_time_hour(self):
    parse = self.parser.parse("every 5 hours at 30 turn heat up", self.context)
    self.assertIsInstance(parse, ScheduleRule)
    self.assertEqual(parse.scheduleStr, "schedule.every(5).hours.at('30')")

