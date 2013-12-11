from Queue import Queue
import logging
import threading
import time
import schedule
from graphitereporter import GraphiteReporter

__logger__ = logging.getLogger("automation-context")
__logger__.setLevel(logging.INFO)

__lock__ = threading.Lock()

class AutomationContext(object):
    def __start_local_threads(self):
        thread = threading.Thread(target=self.__publish_values__)
        thread.daemon = True
        thread.start()
        thread = threading.Thread(target=self.__rule_eval__)
        thread.daemon = True
        thread.start()
        thread = threading.Thread(target=self.__perform_actions__)
        thread.daemon = True
        thread.start()

    def __init__(self, config):
        """
        @type config: config.AutomationConfig
        """
        self.job_queue = Queue()
        self.receivers = {}
        self.values = {}
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
        self.__start_local_threads()

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

    def __publish_values__(self):
        __logger__.info("Starting central value publish thread")
        while True:
            elem = self.publish_queue.get()
            path = elem[0]
            values = elem[1]
            changed = elem[2]
            state = self.values
            for elem in path.split("."):
                if not elem in state:
                    state[elem] = {}
                state = state[elem]
            for key in values:
                if not key in state or not state[key] == values[key]:
                    state[key] = values[key]
                    __logger__.debug("setting %s %s to %s", path, key, state[key])
                    if changed and self.trigger.qsize() == 0:
                        self.trigger.put(True)
            self.publish_queue.task_done()

    def __rule_eval__(self):
        while True:
            self.trigger.get()
            __logger__.debug("State changed, firing rules")
            if self.rule_context: self.rule_context.checkrules()
            else: print 'nope'
            self.trigger.task_done()
            __logger__.debug("done firing rules")

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
            if value:
                return value
        return None

    def getInputValue(self, path):
        return self._getValuePrefixed('input', path)

    def getRuleValue(self, path):
        return self._getValuePrefixed('rule', path)

    def getReceiverValue(self, path):
        return self._getValuePrefixed('receiver', path)

    def _getValuePrefixed(self, prefix, path):
        return self.getValue(self.prefixes[prefix] + path)

    def _getValue(self, path):
        state = self.values
        try:
            for elem in path.split("."):
                state = state[elem]

            return state
        except:
            return None

    def __force_run__(self):
        self.trigger.put(True)

    def start(self):
        self.schedule = schedule.every(10).seconds.do(self.__export_data__)
        self.schedule = schedule.every(10).seconds.do(self.__force_run__)
        self.rule_context.start()

    def stop(self):
        self.rule_context.stop()
