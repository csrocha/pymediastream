from ruamel.yaml import load as yaml_load
from ruamel.yaml import Loader
from pymediastream.yaml import Element, Pipeline




# noinspection PyPep8Naming
def load(stream, loader=Loader):
    pipeline = yaml_load(stream, Loader=loader)
    return pipeline
