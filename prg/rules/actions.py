class Action(object):
  def __init__(self, data):
    self.receiver = data['receiver']
    self.state = data['state']
    self.data = data

  def perform(self, receivers, override = False, overrideOff = False):
    receiver = receivers[self.receiver]
    if overrideOff:
      receiver.setOverrideMode(False)
    elif override:
      receiver.setOverrideMode(True)
    receiver.do(self.state, override)

  def __str__(self):
    return "%s" % self.data
