import subprocess, logging, threading, Queue

jobqueue = Queue.Queue()

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
      jobqueue.put(toexec)
      logging.warn("Turned %s %s" % (self.name, switch))
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

  worker_thread = threading.Thread(target=__worker_main__)
  worker_thread.daemon = True
  worker_thread.start()

  return _receivers

def __worker_main__():
  while True:
    toexec = jobqueue.get()
    logging.warn(toexec)
    subprocess.call(toexec, shell=True)

def receiver(name):
  return _receivers[name]
