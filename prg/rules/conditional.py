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
  def __init__(self, rulename, data, inputs, receivers):
    super(ConditionalRule, self).__init__(rulename, data, inputs, receivers)
    self.conditions = [Condition(condition) for condition in data['conditions']]

  def matches(self):
    return all(condition.matches(self.inputs) for condition in self.conditions)

  def __str__(self):
    return "actions %s\nconditions %s" % (self.actions, self.conditions)
