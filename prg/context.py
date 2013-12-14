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
    def __start_local_threads(self):
        thread = threading.Thread(target=self.__publish_values__)
        thread.daemon = True
        thread.start()
        self.__publish_thread__ = thread
        thread = threading.Thread(target=self.__rule_eval__)
        thread.daemon = True
        thread.start()
        self.__rule_eval_thread__ = thread
        thread = threading.Thread(target=self.__perform_actions__)
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
        self._publishPrefixed('rule', path, values)

    def publishReceiverValues(self, path, values):
        self._publishPrefixed('receiver', path, values)

    def _publishPrefixed(self, prefix, path, values, changed = True):
        self.publishValues(self.prefixes[prefix] + path, values, changed)

    def getValue(self, path):
        for prefix in self.prefixes.values():
            value = self._getValue(prefix + path)
            if not value == None:
                return value
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

    def __force_run__(self):
        self.trigger.put(True)

    def start(self):
        self.receivers.start()
        self.schedule = schedule.every(10).seconds.do(self.__export_data__)
        self.schedule = schedule.every(10).seconds.do(self.__force_run__)
        self.rule_context.start()
        self.inputs.start()
        __logger__.info("Automation started")

    def stop(self):
        self.inputs.stop()
        self.trigger.put(False)
        while self.__rule_eval_thread__.isAlive():
            time.sleep(0.01)
        self.rule_context.stop()

        while self.publish_queue.qsize() >0:
            time.sleep(0.01)

        self.receivers.stop()
        self.save()
        __logger__.info("Automation stopped")

    def save(self):
        filename = "%s/conf/state.json" % self.config.get_basedir()
        with open(filename, 'w') as outfile:
            json.dump(self.values, outfile, indent=4)
        __logger__.info("Stated saved")

    def load(self):
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
            print "Invalid json data"
        __logger__.info("Starting with a clean state")
        return {}

