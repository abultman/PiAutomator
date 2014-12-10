from inputs.inputs import AnInput
from datetime import datetime, timedelta
from astral import Astral
import pytz
import schedule

def init(config):
    pass

class AstralInput(AnInput):
    def __init__(self, name, context, settings):
        super(AstralInput, self).__init__(name, context, settings)
        self.a = Astral()
        self.city = self.a[settings['city']]
        self.schedules = {}

    def start(self):
        super(AstralInput, self).start()
        now = datetime.utcnow().replace(tzinfo = pytz.UTC)
        sunToday = self.city.sun(date = now)
        for type in sunToday:
            self.__schedule_next__(type)

    def __schedule_next__(self, type):
        now = datetime.utcnow().replace(tzinfo = pytz.UTC)
        tomorrow = now + timedelta(days=1)
        sunToday = self.city.sun(date = now)
        sunTomorrow = self.city.sun(date = tomorrow)
        time = sunToday[type]
        if time < now:
            time = sunTomorrow[type]
        schedule_time = "%d:%d" % (time.hour, time.minute)
        self.schedules[type] = schedule.every().day.at(schedule_time).do(self.context.async_perform, self.__update__, type)

    def __update__(self, type):
        self.publish({'state': type})
        schedule.cancel_job(self.schedules[type])
        self.__schedule_next__(type)

    def stop(self):
        super(AstralInput, self).stop()
        for type in self.schedules:
            schedule.cancel_job(self.schedules[type])



