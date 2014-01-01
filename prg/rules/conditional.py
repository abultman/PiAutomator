import logging
from rules import operators, Rule
import ping

__logger__ = logging.getLogger('conditional-rule')
__logger__.setLevel(logging.INFO)

class Condition(object):
    def __init__(self, data):
        self.data = data
        self.input = data['input']
        self.operator = operators[self.data['operator']]
        self.value = self.data['value']
        self.change_time = 0

    def matches(self, automation_context):
        """
        @type automation_context: context.AutomationContext
        """
        sensorValue = automation_context.getValue(self.input)
        if sensorValue:
            self.change_time = sensorValue.change_time
            return self.operator(sensorValue, self.data['value'])
        else:
            return False

    def __str__(self):
        return "%s" % self.data


class ConditionalRule(Rule):
    def __init__(self, rule_context, rule_state, data, nested_rule):
        """
        @type rule_context: rules.RuleContext
        @type rule_state: RuleState
        @type data: matplotlib.pyparsing.ParseResults
        """
        super(ConditionalRule, self).__init__(rule_context, rule_state, data, nested_rule)
        self.conditions = [Condition(condition) for condition in data['conditions']]
        self.always_fire = 'always_fire_rule' in data

    def matches(self):
        return all(condition.matches(self.rule_context.automation_context) for condition in self.conditions)

    def should_rule_fire(self):
        return super(ConditionalRule, self).should_rule_fire() or self.fire_always()

    def max_change_time(self):
        return max(condition.change_time for condition in self.conditions)

    def __str__(self):
        return "%s %s actions %s\nconditions %s" % (
        self.rule_state.rule_id, self.rule_state.rule_name, self.actions, self.conditions)

    def condition_changed(self):
        fire_time = self.rule_state['fire_time']
        return self.max_change_time() > fire_time

    def has_parent(self):
        return self.parent is not None

    def fire_always(self):
        return self.always_fire and (self.condition_changed() or self.has_parent())
