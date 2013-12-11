import dhtreader
from inputs import PollingInput
from timeout import TimeoutError


def init(config):
    dhtreader.init()


class DHT22(PollingInput):
    def __init__(self, name, context, settings):
        super(DHT22, self).__init__(name, context, settings)

    def _read(self):
        try:
            value = dhtreader.read(22, self.settings['pin'])
            if value:
                return {"temperature": value[0], "humidity": value[1]}
        except TimeoutError:
            return None
        return None