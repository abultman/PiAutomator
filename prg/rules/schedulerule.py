import schedule

from rules import Rule


class ScheduleRule(Rule):
    def __init__(self, rule_context, rule_state, data):
        """
        @type rule_state: RuleState
        @type data: matplotlib.pyparsing.ParseResults
        """
        super(ScheduleRule, self).__init__(rule_context, rule_state, data)
        schedule_data = None
        if "pluralSchedule" in data.keys():
            schedule_data = data['pluralSchedule']
        else:
            schedule_data = data['singularSchedule']

        def count():
            if 'count' in schedule_data:
                return schedule_data['count']
            else:
                return 1

        toeval = "schedule.every(%s).%s" % (count(), schedule_data['unit'])
        if "time" in schedule_data.keys():
            toeval = "%s.at('%s')" % (toeval, schedule_data["time"])
        self.scheduleStr = toeval

    def start(self):
        self.schedule = eval(self.scheduleStr).do(self.performActions)

    def __perform_my_actions(self):
        self.rule_context.automation_context.async_perform(self.performActions)

    def stop(self):
        schedule.cancel_job(self.schedule)

    def __str__(self):
        return "actions %s" % (self.actions)


