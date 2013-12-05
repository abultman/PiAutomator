from graphitereporter import *
import Queue,threading, schedule, logging, subprocess

__myclasses__ = {}

__logger__ = logging.getLogger("recievers")
__logger__.setLevel(logging.INFO)

def __load_receiver__(elem, config):
  if elem not in __myclasses__:
    __logger__.info("Loading receiver of type %s" % elem)
    mod = __import__(elem, globals = globals())
    __myclasses__[elem] = getattr(mod, elem)
    if hasattr(mod, 'init'):
      getattr(mod, 'init')(config)
      __logger__.info("Initializing %s" % elem)

  return __myclasses__[elem]

__author__ = 'administrator'

jobqueue = Queue.Queue()

def init(config):
  g = GraphiteReporter(config, "receivers")
  global _receivers
  _receivers = {}
  receivers = config.receivers()
  for name in receivers:
    my_class = __load_receiver__(receivers[name]['type'], config)
    _receivers[name] = my_class(name, config, receivers[name], g)

  worker_thread = threading.Thread(target=__worker_main__)
  worker_thread.daemon = True
  worker_thread.start()

  schedule.every(10).seconds.do(__graphiteReporter__)

  return _receivers

def __graphiteReporter__():
  for receiver in _receivers:
    _receivers[receiver]._sendForReporting()


def __worker_main__():
  while True:
    toexec = jobqueue.get()
    __logger__.info(toexec)
    subprocess.call(toexec, shell=True)

def receiver(name):
  return _receivers[name]
