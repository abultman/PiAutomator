#!/usr/bin/python
import yaml


class AutomationConfig(object):
    def __init__(self, basedir):
        self.basedir = basedir
        with open("%s/conf/config.yaml" % basedir) as f:
            self.yaml = yaml.load(f)

    def get_setting(self, mapList, default=None):
        try:
            return reduce(lambda d, k: d[k], mapList, self.yaml)
        except KeyError as e:
            if default is not None:
                return default
            else:
                raise e

    def inputs(self):
        return self.get_setting(['inputs'])

    def receivers(self):
        return self.get_setting(['receivers'])

    def rules(self):
        return self.get_setting(['rules'])

    def get_basedir(self):
        return self.basedir

class LocalSettings(object):
    def __init__(self, data):
        self.data = data

    def __getitem__(self, key):
        return self.getsetting(key)

    def getsetting(self, key, default = None):
        if key in self.data:
            return self.data[key]
        else:
            return default
