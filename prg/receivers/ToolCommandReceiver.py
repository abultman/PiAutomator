from receivers import *

class ToolCommandReceiver(Receiver):
  def __init__(self, name, config, settings, g):
    super(ToolCommandReceiver, self).__init__(name, config, settings, g)

  def _setState(self, state):
    command = "%s/tools/%s" % (self.config.get_basedir(), self.settings['command'])
    args = "%s %s" % (self.settings['args'], state)
    toexec = "%s %s" % (command, args)
    jobqueue.put(toexec)
