import json
import logging
import socket
from receivers import Receiver

__logger__ = logging.getLogger('pilight-transmitter')
__logger__.setLevel(logging.INFO)

class PiLight(Receiver):
    def __init__(self, name, context, settings):
        super(PiLight, self).__init__(name, context, settings)
        self.host = context.config.getSetting(['pilight', 'host'])
        self.port = context.config.getSetting(['pilight', 'port'])


    def _setState(self, verb, s):
        state = s
        if self.settings['translate-up-down']:
            if state == 'on': state = 'up'
            elif state == 'off': state = 'down'
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.send(json.dumps({'message': 'client controller'}))
        message = {
            'message': 'send',
            'code': {
                'location': self.settings['location'],
                'device': self.settings['device'],
                'state': state,
            }
        }
        __logger__.debug(message)
        s.send(json.dumps(message, ensure_ascii = True))
        s.close()




