import os
import pprint
from os.path import dirname, abspath, isdir

from utils.config import Config
from jsonpath_ng import parse

PP = pprint.PrettyPrinter(indent=4).pprint


class NoCredsError(Exception):
    pass


class BaseSensor(object):
    def __init__(self, name):
        self.name = name
        self.config = Config()
        jsonpath_expr = parse(self.name.replace('/', '.'))
        try:
            self.credentials = [
                x.value
                for x in jsonpath_expr.find(self.config.secrets)
            ][0]
        except:
            raise NoCredsError(f"No credentials defined for {self.name}")

