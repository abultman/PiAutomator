import json
import logging
import socket
from receivers import Receiver

__logger__ = logging.getLogger('pilight-transmitter')
__logger__.setLevel(logging.INFO)

class PiLight(Receiver):
    def __init__(self, name, config, settings, g):
        super(PiLight, self).__init__(name, config, settings, g)
        self.host = config.getSetting(['pilight', 'host'])
        self.port = config.getSetting(['pilight', 'port'])

    def _setState(self, verb, s):
        state = s
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
        __logger__.info(message)
        s.send(json.dumps(message, ensure_ascii = True))
        print s.recv(4096)
        s.close()




