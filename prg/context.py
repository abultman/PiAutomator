from Queue import Queue
import json
import logging
import pickle
import threading
import time
import schedule
from graphitereporter import GraphiteReporter

PREVIOUS_VALUE = "_previous_value"
CHANGE_TIME = "_change_time"

__logger__ = logging.getLogger("automation-context")
__logger__.setLevel(logging.INFO)

__lock__ = threading.Lock()

class AutomationContext(object):
    def __start_publish_queue__(self):
        thread = threading.Thread(target=self.__publish_values__, name='publish-values')
        thread.daemon = True
        thread.start()
        self.__publish_thread__ = thread
        return thread

    def __start_local_threads(self):
        self.__start_publish_queue__()
        thread = threading.Thread(target=self.__rule_eval__, name='rule-eval')
        thread.daemon = True
        thread.start()
        self.__rule_eval_thread__ = thread
        thread = threading.Thread(target=self.__perform_actions__, name='job-function-executor')
        thread.daemon = True
        thread.start()
        self.__action_thread__ = thread

    def __init__(self, config):
        """
        @type config: config.AutomationConfig
        """
        self.job_queue = Queue()
        self.receivers = {}
        self.prefixes = {
            'root': '',
            'input': 'input.',
            'rule':'rule.',
            'receiver': 'receiver.'
        }
        self.trigger = Queue()
        self.config = config
        self.receivers = None
        self.rule_context = None
        self.publish_queue = Queue(100)
        self.reporter = GraphiteReporter(config)
        self.values = self.load()

    def __export_data__(self):
        self.__export_data_path__("automation_context", self.values)

    def __export_data_path__(self, path, values):
        def is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False
        if path.endswith(CHANGE_TIME) or path.endswith(PREVIOUS_VALUE):
            # don't publish calculated values
            # deprecated, should be removed soon
            return

        if isinstance(values, dict):
            for key in values:
                self.__export_data_path__(path + "." + key, values[key])
        elif isinstance(values, Value):
            self.__export_data_path__(path, values.value)
        elif is_number(values):
            self.reporter.send(path, values)
        elif values == True:
            self.reporter.send(path, 1)
        elif values == False:
            self.reporter.send(path, 0)
        elif values == "ON":
            self.reporter.send(path, 1)
        elif values == "OFF":
            self.reporter.send(path, 0)

    def publishOne(self, elem, get_value):
        path = elem[0]
        values = elem[1]
        changed = elem[2]
        change_time = time.time()
        state = self.values
        for elem in path.split("."):
            if not elem in state:
                state[elem] = {}
            state = state[elem]
        for key in values:
            if not key in state or not state[key] == values[key] or changed:
                assignable = get_value(values[key])

                old_value = None
                if key in state:
                    old_value = get_value(state[key])

                state[key] = Value(assignable, change_time, old_value)
                __logger__.debug("setting %s %s to %s", path, key, state[key])
                if self.trigger.qsize() == 0:
                    __logger__.debug("Triggering due to path %s", path)
                    self.trigger.put(True)
        self.publish_queue.task_done()

    def __publish_values__(self):
        def get_value(orig):
            if isinstance(orig, Value):
                return orig.value
            return orig

        __logger__.info("Starting central value publish thread")
        while True:
            elems = []
            elems.append(self.publish_queue.get())
            size = 0
            maxIt = self.publish_queue.qsize()
            no_exception = True
            while size < maxIt and no_exception:
                try:
                    elems.append(self.publish_queue.get_nowait())
                    size = size + 1
                except Queue.Empty, e:
                    no_exception = False
            __logger__.debug('publishing %d items', size)
            for elem in elems:
                self.publishOne(elem, get_value)
            time.sleep(0.001)

    def __rule_eval__(self):
        while True:
            if not self.trigger.get():
                break

            # wait a while to give other values a chance to catch up
            time.sleep(0.01)
            __logger__.debug("State changed, firing rules")
            if self.rule_context: self.rule_context.checkrules()
            self.trigger.task_done()
            __logger__.debug("done firing rules")
        __logger__.info("rule thread terminated")

    def __perform_actions__(self):
        while True:
            job = self.job_queue.get()
            job()
            self.job_queue.task_done()

    def async_perform(self, fun):
        self.job_queue.put(fun)

    def publishValues(self, path, values, changed = True):
        self.publish_queue.put([path, values, changed])
        __logger__.debug("added %s for path %s", values, path)

    def publishInputValues(self, path, values):
        self._publishPrefixed('input', path, values)

    def publishRuleValues(self, path, values):
        self._publishPrefixed('rule', path, values, False)

    def publishReceiverValues(self, path, values):
        self._publishPrefixed('receiver', path, values)

    def _publishPrefixed(self, prefix, path, values, changed = True):
        self.publishValues(self.prefixes[prefix] + path, values, changed)

    def getValue(self, path):
        for prefix in self.prefixes.values():
            value = self._getValue(prefix + path)
            if isinstance(value, Value):
                return value
            elif not value == None:
                # Old style, deprecated
                change_time = self._getValue(prefix + path + CHANGE_TIME)
                previous_value = self._getValue(prefix + path + PREVIOUS_VALUE)
                return Value(value, change_time, previous_value)
        return None

    def getInputValue(self, path):
        return self._getValuePrefixed('input', path)

    def getRuleValue(self, path = ''):
        return self._getValuePrefixed('rule', path)

    def getReceiverValue(self, path):
        return self._getValuePrefixed('receiver', path)

    def _getValuePrefixed(self, prefix, path):
        return self.getValue(self.prefixes[prefix] + path)

    def _getValue(self, path):
        state = self.values
        try:
            for elem in path.split("."):
                if elem == '': break
                state = state[elem]

            return state
        except:
            return None

    def __scheduled_stuff__(self):
        if self.config.get_setting(['automator', 'periodic-rule-eval'], False):
            self.trigger.put(True)
        if self.config.get_setting(['automator', 'periodic-state-save'], False):
            self.async_perform(self.save)

    def start(self):
        self.receivers.start()
        self.schedule = schedule.every(self.config.get_setting(['automator', 'reporting-interval'], 10)).seconds.do(self.__export_data__)
        self.schedule = schedule.every(10).seconds.do(self.__scheduled_stuff__)
        self.rule_context.start()
        self.inputs.start()

        self.__start_local_threads()
        self.publishValues("automationcontext", {'started': True})
        __logger__.info("Automation started")

    def stop(self):
        self.publishValues("automationcontext", {'started': False})
        self.inputs.stop()
        self.trigger.put(False)
        while self.__rule_eval_thread__.isAlive():
            time.sleep(0.01)
        self.rule_context.stop()

        while self.publish_queue.qsize() >0:
            time.sleep(0.01)

        while self.job_queue.qsize() >0:
            time.sleep(0.01)

        self.receivers.stop()
        self.save()
        __logger__.info("Automation stopped")

    def __state_file__(self):
        return "%s/conf/state.json" % self.config.get_basedir()

    def save(self):
        if self.config.get_setting(['automator', 'save-state'], True):
            __lock__.acquire()
            try:
                filename = self.__state_file__()
                with open(filename, 'w') as outfile:
                    json.dump(self.values, outfile, indent=4)
                __logger__.debug("Stated saved")
            finally:
                __lock__.release()

    def load(self):
        if self.config.get_setting(['automator', 'save-state'], True):
            try:
                filename = self.__state_file__()
                with open(filename, 'r') as outfile:
                    values = json.load(outfile)
                    __logger__.info("Stated loaded")
                    return values
            except IOError as ioe:
                if ioe.errno == 2:
                    __logger__.info("no state file detected")
                else:
                    __logger__.error("Stated not loaded due to IOError")
                    __logger__.exception(ioe)
            except ValueError:
                __logger__.warn("Stated not loaded due invalid json format in state file")
            __logger__.info("Starting with a clean state")
        return {}

class Value(object):
    def __init__(self, value = None, change_time = None, previous_value = None):
        self.value = value
        self.change_time = change_time
        self.previous_value = previous_value

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return self.value != (other)

    def __abs__(self):
        return abs(self.value)

    def __cmp__(self, other):
        return cmp(self.value, other)

    def __and__(self, other):
        self.value.__and__(other)

    def __iter__(self):
        return self.value.__iter__()

    def __getitem__(self, key):
        return self.value.__getitem__(key)

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __str__(self):
        return str(self.value)

    def __add__(self, other):
        return self.value + other

    def __mul__(self, other):
        return self.value * other

    def __div__(self, other):
        return self.value / other

    def pop(self, item, default=None):
        return self.value.pop(item, default)

    def __repr__(self):
        return "[Value: %s, %s ,%s]" % (self.value, self.change_time, self.previous_value)

    def __str__(self):
        return str(self.value)



def _jsonSupport( *args ):
    def default( self, xObject ):
        return { 'type': 'context.Value', 'value': xObject.__dict__ }

    def objectHook( obj ):
        if 'type' not in obj:
            return obj
        if obj[ 'type' ] != 'context.Value':
            return obj
        val = Value()
        for key in obj['value']:
            val.__setattr__(key, obj['value'][key])
        return val

    json.JSONEncoder.default = default
    json._default_decoder = json.JSONDecoder(object_hook = objectHook)

_jsonSupport()
