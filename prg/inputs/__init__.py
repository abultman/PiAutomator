from graphitereporter import *
import Queue,threading, schedule, logging

__myclasses__ = {}

__logger__ = logging.getLogger("inputs")
__logger__.setLevel(logging.INFO)

def __load_receiver__(elem, config):
  if elem not in __myclasses__:
    __logger__.info("Loading input of type %s" % elem)
    mod = __import__(elem, globals = globals())
    __myclasses__[elem] = getattr(mod, elem)
    if hasattr(mod, 'init'):
      getattr(mod, 'init')(config)
      __logger__.info("Initializing %s" % elem)

  return __myclasses__[elem]

jobqueue = Queue.Queue()

def __worker_main__():
  while True:
    jobqueue.get()()

def init(config):
  g = GraphiteReporter(config)
  global _inputs
  _inputs = {}
  inputs = config.inputs()
  for name in inputs:
    my_class = __load_receiver__(inputs[name]['type'], config)
    _inputs[name] = my_class(name, inputs[name], g)
    _inputs[name].refresh()
    schedule.every(10).seconds.do(jobqueue.put, _inputs[name].refresh)

  worker_thread = threading.Thread(target=__worker_main__)
  worker_thread.daemon = True
  worker_thread.start()

  return _inputs
