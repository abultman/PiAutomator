from Queue import Queue
import json
import logging
import threading
import time
import schedule
from graphitereporter import GraphiteReporter

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
        self.publish_queue = Queue()
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

        if isinstance(values, dict):
            for key in values:
                self.__export_data_path__(path + "." + key, values[key])
        elif is_number(values):
            self.reporter.send(path, values)
        elif values == True:
            self.reporter.send(path, 1)
        elif values == False:
            self.reporter.send(path, 0)

    def __publish_values__(self):
        __logger__.info("Starting central value publish thread")
        while True:
            elem = self.publish_queue.get()
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
                    assignable = values[key]
                    if isinstance(assignable, Value):
                        assignable = assignable.value
                    state[key] = assignable
                    state[key + "_change_time"] = change_time
                    __logger__.debug("setting %s %s to %s", path, key, state[key])
                    if self.trigger.qsize() == 0:
                        self.trigger.put(True)
            self.publish_queue.task_done()

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
            if not value == None:
                change_time = self._getValue(prefix + path + "_change_time")
                return Value(value, change_time)
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
        if self.config.getSetting(['automator', 'periodic-rule-eval'], False):
            self.trigger.put(True)
        if self.config.getSetting(['automator', 'periodic-state-save'], False):
            self.async_perform(self.save)

    def start(self):
        self.receivers.start()
        self.schedule = schedule.every(self.config.getSetting(['automator', 'reporting-interval'], 10)).seconds.do(self.__export_data__)
        self.schedule = schedule.every(10).seconds.do(self.__scheduled_stuff__)
        self.rule_context.start()
        self.inputs.start()

        self.__start_local_threads()
        __logger__.info("Automation started")

    def stop(self):
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

    def save(self):
        if self.config.getSetting(['automator', 'save-state'], True):
            __lock__.acquire()
            try:
                filename = "%s/conf/state.json" % self.config.get_basedir()
                with open(filename, 'w') as outfile:
                    json.dump(self.values, outfile, indent=4)
                __logger__.debug("Stated saved")
            finally:
                __lock__.release()

    def load(self):
        if self.config.getSetting(['automator', 'save-state'], True):
            try:
                filename = "%s/conf/state.json" % self.config.get_basedir()
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
    def __init__(self, value, change_time):
        self.value = value
        self.change_time = change_time

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
