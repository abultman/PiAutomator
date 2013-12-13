import logging
import urllib
import urllib2

from receivers import Receiver


class ProwlInitializtionError(Exception):
    pass


class ProwlReceiver(Receiver):
    def __init__(self, name, context, settings):
        super(ProwlReceiver, self).__init__(name, context, settings)
        self.api_key = settings['api-key']
        self.application = settings['application']
        self.verify()

    def perform_for_state(self, verb, state):
        values = {
            "apikey": self.api_key,
            "application": self.application,
            "description": state
        }
        data = urllib.urlencode(values)
        try:
            urllib2.urlopen("https://api.prowlapp.com/publicapi/add", data)
        except urllib2.HTTPError as e:
            logging.error('The server couldn\'t fulfill the request.')
            logging.error('Error code: %s' % e.code)
        except urllib2.URLError as e:
            logging.error('We failed to reach a server.')
            logging.error('Reason: %s' % e.reason)

    def verify(self):
        try:
            urllib2.urlopen("https://api.prowlapp.com/publicapi/verify?apikey=%s" % self.api_key)
        except:
            raise ProwlInitializtionError("Passed api key is not valid")