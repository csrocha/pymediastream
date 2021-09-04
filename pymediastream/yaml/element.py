from typing import Any
from ruamel.yaml import Loader, Dumper, YAMLObject
from ruamel.yaml import ScalarNode, MappingNode
from gi.repository import Gst
from .base import WithProperties
from .pad import Pad
from .joiner import joiner


def on_pad_added(src, new_pad):
    ref = f"{src.name}:{new_pad.name}"
    print(f"Created new pad {ref}")
    if ref in joiner:
        joiner.join_lazy(ref)
    Pad.setup_lazy(ref)


class Element(WithProperties, YAMLObject):
    yaml_dumper = Dumper
    yaml_loader = Loader

    yaml_tag = None
    element_name = None

    def __init__(self, element):
        self._element = element

    def _with_property(self, key=None):
        if key:
            return self.get_pad(key)
        else:
            return self._element

    @property
    def name(self):
        return self._element.name

    def get_element(self):
        return self._element

    def get_srcpads(self):
        return self._element.srcpads

    def get_sinkpads(self):
        return self._element.sinkpads

    def get_pad(self, pad_name):
        pad = next((pad for pad in self._element.pads if pad.name == pad_name), None)
        if not pad:
            pad_template = self._element.get_pad_template(pad_name)
            pad = self._element.request_pad(pad_template, None, None) if pad_template else None
        return Pad(self, pad_name, pad=pad)

    def get_unlinked_pad(self):
        pad = next((pad for pad in self._element.pads if not pad.is_linked()), None)
        return Pad(self, pad.name, pad=pad) if pad else None

    def get_unlinked_srcpad(self):
        pad = next((pad for pad in self._element.srcpads if not pad.is_linked()), None)
        return Pad(self, pad.name, pad=pad) if pad else None

    def get_unlinked_sinkpad(self):
        pad = next((pad for pad in self._element.sinkpads if not pad.is_linked()), None)
        return Pad(self, pad.name, pad=pad) if pad else None

    def connect(self, event_name, callback):
        return self._element.connect(event_name, callback)

    def link_pads_filtered(self, pad: Pad, target_element: 'Element', target_pad: Pad, caps: Any):
        return self._element.link_pads_filtered(
            pad and pad.name,
            target_element._element,
            target_pad and target_pad.name,
            caps
        )

    def link_pads(self, pad: Pad, target_element: 'Element', target_pad: Pad):
        return self._element.link_pads(
            pad and pad.name,
            target_element._element,
            target_pad and target_pad.name
        )

    @classmethod
    def from_yaml(cls, loader, node):
        element = cls(Gst.ElementFactory.make(cls.element_name, node.anchor))
        print(f"Creating element {cls.element_name} as {node.anchor}")

        assert element is not None, f"cls.element_name: {cls.element_name}"

        if isinstance(node, ScalarNode):
            pass
        elif isinstance(node, MappingNode):
            attributes = loader.construct_mapping(node, deep=True)
            element.set_properties(attributes)

        element.connect('pad-added', on_pad_added)

        return element

    @classmethod
    def to_yaml(cls, dumper, data):
        return None

    @staticmethod
    def get_elements():
        Gst.init()
        reg = Gst.Registry.get()
        return [f.get_name() for f in reg.get_feature_list(Gst.ElementFactory)]

    @classmethod
    def build_element_classes(cls):
        element_class = {}
        for element in cls.get_elements():
            element_class[element] = type(element, (cls,), {
                'yaml_tag': f'!{element}',
                'element_name': f'{element}',
            })
        return element_class


