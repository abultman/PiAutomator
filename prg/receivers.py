import subprocess, logging

class Receiver(object):
  def __init__(self, name, config, settings):
    self.settings = settings
    self.name = name
    self.config = config
    self.state = None

  def do(self, switch):
    if self.state != switch or self.state == None:
      command = "%s/tools/%s" % (self.config.get_basedir(), self.settings['type'])
      args = "%s %s" % (self.settings['command'], switch)
      toexec = "%s %s" % (command, args)
      subprocess.call(toexec, shell=True)
      logging.info("Turned %s %s" % (self.name, switch))
    self.state = switch

  def off(self):
    self.do('off')

  def on(self):
    self.do('on')

def init(config):
  global _receivers
  _receivers = {}
  receivers = config.receivers()
  for name in receivers:
    _receivers[name] = Receiver(name, config, receivers[name])

  return _receivers

def receiver(name):
  return _receivers[name]
