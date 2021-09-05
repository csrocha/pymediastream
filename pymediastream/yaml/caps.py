from ruamel.yaml import Loader, Dumper, YAMLObject
from gi.repository import Gst


class Caps(YAMLObject):
    yaml_dumper = Dumper
    yaml_loader = Loader

    yaml_tag = u'!Caps'

    @classmethod
    def from_yaml(cls, loader, node):
        caps_string = loader.construct_scalar(node)
        return Gst.Caps.from_string(caps_string)
