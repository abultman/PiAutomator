from core import SCOPE_INPUT
import dhtreader
from inputs.inputs import PollingInput
from timeout import TimeoutError

def init_module(config):
    dhtreader.init()


class DHT(PollingInput):
    def __init__(self, name, context, settings):
        super(DHT, self).__init__(name, context, settings)
        self.type = settings.getsetting('dhttype', 22)

    def _read(self):
        try:
            value = dhtreader.read(self.type, self.settings['pin'])
            if value:
                return {"temperature": value[0], "humidity": value[1]}
        except TimeoutError:
            return None
        return None

def factory(name, context, settings):
    return DHT(name, context,settings)

config = {SCOPE_INPUT: factory}