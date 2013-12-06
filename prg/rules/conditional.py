from rules import _operators, Rule

class Condition(object):
  def __init__(self, data):
    self.data = data
    self.sensor = data['sensor']
    self.metric = data['metric']
    self.operator = _operators[self.data['operator']]
    self.value = self.data['value']

  def matches(self, inputs):
    sensor = inputs[self.sensor]
    sensorValue = sensor.get(self.metric)
    if sensorValue:
      return self.operator(sensorValue, self.data['value'])
    else:
      return False

  def __str__(self):
    return "%s" % self.data

class ConditionalRule(Rule):
  def __init__(self, rule_context, rule_state, data):
    """
    @type rule_state: RuleState
    @type data: matplotlib.pyparsing.ParseResults
    """
    super(ConditionalRule, self).__init__(rule_context, rule_state, data)
    self.conditions = [Condition(condition) for condition in data['conditions']]

  def matches(self):
    return all(condition.matches(self.rule_context.inputs) for condition in self.conditions)

  def __str__(self):
    return "%s %s actions %s\nconditions %s" % (self.rule_state.rule_id, self.rule_state.rule_name, self.actions, self.conditions)
