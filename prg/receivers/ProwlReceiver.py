import logging
import urllib
from receivers import Receiver
import urllib2

class ProwlInitializtionError(Exception):
  pass

class ProwlReceiver(Receiver):
  def __init__(self,  name, config, settings, g):
    super(ProwlReceiver, self).__init__(name, config, settings, g)
    self.api_key = settings['api-key']
    self.application = settings['application']
    # self.verify()

  def _setState(self, verb, state):
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




# ProwlReceiver("me", {}, {"api-key":"1247cee2d6796e96e893a24d7967395b5f5a7286", "application": "homeautomation"}, {})._setState("Works!")