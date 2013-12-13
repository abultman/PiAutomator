import logging
import schedule
from actions import Action

operators = {
    "less than": lambda x, y: int(x) < int(y),
    "greater than": lambda x, y: int(x) > int(y),
    "equal to": lambda x, y: str(x) == str(y)
}

__logger__ = logging.getLogger(("rules"))
__logger__.setLevel(logging.INFO)

class RuleState(object):
    def __init__(self, rule_id, rule_name, context):
        """
        @type context: RuleContext
        """
        def get_value(name):
            value = context.automation_context.getRuleValue(rule_id + "." + name)
            if value == None:
                return 0
            return value

        self.context = context
        self.data = {
            "total_fired_count": get_value("total_fired_count"),
            "total_success_count": get_value("total_success_count"),
            "total_failed_count": get_value("total_failed_count"),
            "success_state": get_value("success_state"),
            "failed_state": get_value("failed_state")
        }
        self.rule_id = rule_id
        self.rule_name = rule_name

    def success(self):
        if self.data["success_state"] == 0:
            self.incr("total_fired_count")
            self.incr("total_success_count")
            self.data["success_state"] = 1
            self.reset("failed_state")

    def failed(self):
        if self.data["failed_state"] == 0:
            self.incr("total_fired_count")
            self.incr("total_failed_count")
            self.data["failed_state"] = 1
            self.reset("success_state")

    def __getitem__(self, item):
        return self.data[item]

    def reset(self, name):
        self.data[name] = 0

    def incr(self, name):
        if name in self.data:
            self.data[name] = self.data[name] + 1
        else:
            self.data[name] = 1


class Rule(object):
    def __init__(self, rule_context, rule_state, data):
        """
        @type rule_state: RuleState
        @type rule_context: RuleContext
        @type data: matplotlib.pyparsing.ParseResults
        """
        self.actions = [Action(action) for action in data['actions']]
        self.override = "override" in data
        self.overrideOff = False
        if self.override and len(data["override"]) == 1:
            warning = "rule '%s' has override configuration and will turn a possible override state off"
            self.overrideOff = True
            __logger__.info(warning % rule_state.rule_name)
        elif self.override:
            __logger__.info(
                "rule '%s' has override configuration and will turn a possible override state on" % rule_state.rule_name)
        self.rule_state = rule_state
        self.rule_context = rule_context

    def matches(self):
        return False

    def performActions(self):
        def should_rule_fire():
            return self.rule_state['success_state'] == 0

        if should_rule_fire():
            [action.perform(self.rule_context, self.rule_state, self.override, self.overrideOff) for action in self.actions]
            self.rule_state.success()
            __logger__.debug('fired %s', self.rule_state.rule_name)

    def publish(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass


class RuleContext(object):
    def __init__(self, automation_context):
        """
        @type automation_context: context.AutomationContext
        """
        self.rules = {}
        self.started = False
        self.automation_context = automation_context

    def add_rule(self, rule):
        """
        @type rule: rules.Rule
        """
        self.rules[rule.rule_state.rule_id] = rule
        if self.started:
            rule.start()

    def start(self):
        self.started = True
        [rule.start() for rule in self.rules.values()]
        rule_values = self.automation_context.getRuleValue()
        rules_to_delete = []
        for rule_id in rule_values:
            if rule_id not in self.rules:
                rules_to_delete.append(rule_id)
        for rule_id in rules_to_delete:
            rule_values.pop(rule_id)
        __logger__.info("Rule context started")


    def stop(self):
        [rule.stop() for rule in self.rules.values()]
        __logger__.info("Rule context stopped")

    def checkrules(self):
        self.findMatchingRules().andPerformTheirActions()
        for rule in self.rules:
            self.automation_context.publishRuleValues(rule, self.rules[rule].rule_state.data)

    def findMatchingRules(self):
        def rulesMatchingInputs():
            for rule in self.rules.values():
                if rule.matches():
                    yield rule
                else:
                    rule.rule_state.failed()

        return MatchingRules(rulesMatchingInputs())


class MatchingRules(object):
    def __init__(self, matchingRules):
        self.matchingRules = matchingRules

    def andPerformTheirActions(self):
        for rule in self.matchingRules:
            rule.performActions()



