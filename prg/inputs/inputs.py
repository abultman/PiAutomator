import logging


class AnInput(object):
  def __init__(self, name, settings, g):
    self.settings = settings
    self.g = g
    self.name = name

  def refresh(self):
    logging.debug("refreshing %s" % self.name)
    self.value = self._read()
    if self.value:
      logging.info("refreshed %s: %s" % (self.name, self.value))
      if isinstance(self.value, dict):
        for key in self.value:
          self.g.send('%s.%s' % (self.name, key), self.value[key])
      else:
        self.g.send('%s.value' % (self.name), self.value)

  def _read(self):
    return None

  def get(self, name=None):
    if self.value:
      if name != None and isinstance(self.value, dict):
        return self.value[name]
      else:
        return self.value
    return None


