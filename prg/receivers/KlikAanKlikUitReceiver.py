#!/usr/bin/python
from __future__ import with_statement
from array import array
import receivers
import wiringpi2

__pin__ = 15
__repeats__ = 3

class WiringError(Exception):
    pass

def init(config):
  KlikAanKlikUitReceiver.__pin__ = int(config.getSetting(['kaku', 'pin']))
  KlikAanKlikUitReceiver.__repeats__ = int(config.getSetting(['kaku', 'repeats']))
  if wiringpi2.wiringPiSetup() == -1:
    raise WiringError("Unable to init wiringpi")

class KlikAanKlikUitReceiver(receivers.Receiver):
  def __init__(self,  name, config, settings, g):
    super(KlikAanKlikUitReceiver, self).__init__(name, config, settings, g)
    self.pin = __pin__
    self.repeats = __repeats__

  def __encode_telegram(self, trits):
    data = 0
    for elem in trits:
      data = data * 3
      data = data + elem

    return data

  def __get_telegram(self, address, device, state):
    actual_address = ord(address) - 65
    actual_device = device - 1

    trits = array('H')

    for i in range(0,4):
      if actual_address & 1:
        trits.append(2)
      else:
        trits.append(0)
      actual_address>>=1

    for i in range(0,4):
      if actual_device & 1:
        trits.append(2)
      else:
        trits.append(0)
      actual_device>>=1

    trits.append(0)
    trits.append(2)
    trits.append(2)

    if state:
      trits.append(2)
    else:
      trits.append(0)

    return self.__encode_telegram(trits)

  def __send_telegram(self, telegram):
    wait = 375
    data = 0
    for i in range(0, 12):
      data<<=2
      data |= telegram %3
      telegram /= 3

    for i in range(0, self.repeats):
      repeatData = data
      for j in range(0, 12):
        test = repeatData & 3
        if test ==0:
          wiringpi2.digitalWrite(self.pin, 1)
          wiringpi2.delayMicroseconds(wait)
          wiringpi2.digitalWrite(self.pin, 0)
          wiringpi2.delayMicroseconds(wait * 3)
          wiringpi2.digitalWrite(self.pin, 1)
          wiringpi2.delayMicroseconds(wait)
          wiringpi2.digitalWrite(self.pin, 0)
          wiringpi2.delayMicroseconds(wait * 3)
        elif test == 1:
          wiringpi2.digitalWrite(self.pin, 1)
          wiringpi2.delayMicroseconds(wait * 3)
          wiringpi2.digitalWrite(self.pin, 0)
          wiringpi2.delayMicroseconds(wait)
          wiringpi2.digitalWrite(self.pin, 1)
          wiringpi2.delayMicroseconds(wait * 3)
          wiringpi2.digitalWrite(self.pin, 0)
          wiringpi2.delayMicroseconds(wait)
        elif test == 2:
          wiringpi2.digitalWrite(self.pin, 1)
          wiringpi2.delayMicroseconds(wait)
          wiringpi2.digitalWrite(self.pin, 0)
          wiringpi2.delayMicroseconds(wait * 3)
          wiringpi2.digitalWrite(self.pin, 1)
          wiringpi2.delayMicroseconds(wait * 3)
          wiringpi2.digitalWrite(self.pin, 0)
          wiringpi2.delayMicroseconds(wait)

        repeatData >>= 2

      wiringpi2.digitalWrite(self.pin, True)
      wiringpi2.delayMicroseconds(wait)
      wiringpi2.digitalWrite(self.pin, False)
      wiringpi2.delayMicroseconds(wait * 31)

  def _setState(self, verb, state):
    self.send_signal(self.settings['address'], int(self.settings['device']), state == 'on')

  def send_signal(self, address, device, state):
    # output and loway
    wiringpi2.pinMode(self.pin, 1)
    wiringpi2.digitalWrite(self.pin, 0)
    self.__send_telegram(self.__get_telegram(address, device, state))
