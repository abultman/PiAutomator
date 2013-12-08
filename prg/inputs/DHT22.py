import dhtreader
from inputs import AnInput
from timeout import TimeoutError


def init(config):
    dhtreader.init()


class DHT22(AnInput):
    def __init__(self, name, settings, g):
        super(DHT22, self).__init__(name, settings, g)
        self.settings = settings
        self.g = g

    def _read(self):
        try:
            value = dhtreader.read(22, self.settings['pin'])
            if value:
                return {"temperature": value[0], "humidity": value[1]}
        except TimeoutError:
            return None
        return None