from ruamel.yaml import Loader, Dumper, YAMLObject
from .base import WithProperties


class Pad(WithProperties, YAMLObject):
    yaml_dumper = Dumper
    yaml_loader = Loader

    yaml_tag = u'!Pad'

    __lazy__ = {}

    def __init__(self, element, pad_name, setup=None, pad=None):
        self._element = element
        self._pad_name = pad_name
        self._setup = setup or {}
        self._pad = pad

    def _with_property(self, key=None):
        assert self._pad
        return self._pad

    def is_valid(self):
        return self._pad is not None

    @property
    def name(self):
        return self._pad_name

    @property
    def element(self):
        return self._element

    def init(self):
        if not self.is_valid():
            self._pad = self._element.get_pad(self._pad_name)

    def setup(self, values=None):
        if self.is_valid():
            self.set_properties(values or self._setup or {})
        else:
            ref = f"{self._element.name}:{self._pad_name}"
            self.__lazy__[ref] = self

        self._setup = values or self._setup or {}

    @classmethod
    def setup_lazy(cls, ref):
        pad = cls.__lazy__.get(ref)
        if pad:
            pad.init()
            pad.setup()
            del cls.__lazy__[ref]
        else:
            print(f"Unexpected lazy setup: {ref}")

    @classmethod
    def from_yaml(cls, loader, node):
        pad_description = loader.construct_mapping(node, deep=True)
        element = pad_description['element']
        pad_name = pad_description['pad_name']
        setup = pad_description.get('setup', None)

        pad = element.get_pad(pad_name)
        pad.setup(setup)

        return pad
