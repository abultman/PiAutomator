import logging
import random


def init():
  None

def read(type, pin):
  result = [random.randint(10,25), random.randint(45, 95)]
  logging.warn("sensor reading: %s" % result)
  return result