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
        self.changed = False
        self.config = config
        self.receivers = None
        self.rule_context = None
        self.publish_queue = Queue()
        self.__start_local_threads()
        self.reporter = GraphiteReporter(config)

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
            print "reporting %s: %s" % (path, values)
            self.reporter.send(path, values)

    def __publish_values__(self):
        __logger__.info("Starting central value publish thread")
        while True:
            elem = self.publish_queue.get()
            path = elem[0]
            values = elem[1]
            state = self.values
            for elem in path.split("."):
                if not elem in state:
                    state[elem] = {}
                state = state[elem]
            for key in values:
                if not key in state or not state[key] == values[key]:
                    state[key] = values[key]
                    __logger__.info("setting %s %s to %s", path, key, state[key])
                    self.changed = True
            self.publish_queue.task_done()

    def __rule_eval__(self):
        while True:
            if self.changed and self.rule_context:
                self.changed = False
                __logger__.info("State changed, firing rules")
                self.rule_context.checkrules()
                __logger__.info("done firing rules")
            else:
                time.sleep(0)

    def __perform_actions__(self):
        while True:
            job = self.job_queue.get()
            job()
            self.job_queue.task_done()

    def async_perform(self, fun):
        self.job_queue.put(fun)

    def publishValues(self, path, values):
        self.publish_queue.put([path, values])
        __logger__.debug("added %s for path %s", values, path)

    def publishInputValues(self, path, values):
        self._publishPrefixed('input', path, values)

    def publishRuleValues(self, path, values):
        self._publishPrefixed('rule', path, values)

    def publishReceiverValues(self, path, values):
        self._publishPrefixed('receiver', path, values)

    def _publishPrefixed(self, prefix, path, values):
        self.publishValues(self.prefixes[prefix] + path, values)

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

    def start(self):
        self.schedule = schedule.every(10).seconds.do(self.__export_data__)
        self.rule_context.start()

    def stop(self):
        self.rule_context.stop()
