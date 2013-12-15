import schedule

from rules import Rule


class ScheduleRule(Rule):
    def __init__(self, rule_context, rule_state, data):
        """
        @type rule_state: RuleState
        @type data: matplotlib.pyparsing.ParseResults
        """
        weekdays = ['monday', 'tuesday', 'wednesday','thursday','friday']
        weekenddays = ['saturday', 'sunday']

        super(ScheduleRule, self).__init__(rule_context, rule_state, data)
        self.scheduleStr = []
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

        def schedule(unit):
            toeval = "schedule.every(%s).%s" % (count(), unit)
            if "time" in schedule_data.keys():
                toeval = "%s.at('%s')" % (toeval, schedule_data["time"])
            self.scheduleStr.append(toeval)

        unit = schedule_data['unit']
        if unit == 'weekday':
            [schedule(day) for day in weekdays]
        elif unit == 'weekendday':
            [schedule(day) for day in weekenddays]
        elif hasattr(unit, 'asList'):
            [schedule(day) for day in unit.asList()]
        else:
            schedule(unit)

    def start(self):
        self.schedule = [eval(sched).do(self.performActions) for sched in self.scheduleStr]

    def __perform_my_actions(self):
        self.rule_context.automation_context.async_perform(self.performActions)

    def stop(self):
        self.schedule = [schedule.cancel_job(sched) for sched in self.schedule]

    def __str__(self):
        return "actions %s" % (self.actions)


