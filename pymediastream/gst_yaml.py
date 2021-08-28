import os
from typing import Any
from ruamel.yaml import load as yaml_load
from ruamel.yaml import Loader, Dumper, YAMLObject
from ruamel.yaml import ScalarNode, MappingNode
from gi.repository import Gst
from .joiner import Joiner


joiner = Joiner()


def on_pad_added(src, new_pad):
    ref = f"{src.name}:{new_pad.name}"
    print(f"Created new pad {ref}")
    if ref in joiner:
        joiner.join_lazy(ref)


class WithProperties:
    def _with_property(self, key=None):
        raise NotImplemented

    def set_property(self, key: str, value: Any):
        if isinstance(value, str):
            value = os.path.expandvars(value)
        print(f"\t{key} as {value}")
        self._with_property().set_property(
            key,
            value
        )

    def set_properties(self, values: dict):
        for key, value in values.items():
            if isinstance(value, dict):
                sub_with_property = self._with_property(key)
                if sub_with_property:
                    sub_with_property.set_properties(value)
            else:
                self.set_property(key, value)


class Pad(WithProperties, YAMLObject):
    yaml_dumper = Dumper
    yaml_loader = Loader

    yaml_tag = u'!Pad'

    def __init__(self, element, pad_name, setup=None, pad=None):
        self._element = element
        self._pad_name = pad_name
        self._setup = setup
        self._pad = pad

    def _with_property(self, key=None):
        return self._pad

    def is_valid(self):
        return self._pad is not None

    @property
    def name(self):
        return self._pad_name

    @property
    def element(self):
        return self._element

    @classmethod
    def from_yaml(cls, loader, node):
        pad_description = loader.construct_mapping(node, deep=True)
        element = pad_description['element']
        pad_name = pad_description['pad_name']
        setup = pad_description.get('setup', None)

        pad = element.get_pad(pad_name)
        if pad.is_valid():
            if setup:
                pad.set_properties(setup)
                pad._setup = setup
        else:
            pad = cls(element, pad_name, setup)

        assert pad

        return pad


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
        return self._element.link_pads_filtered(pad and pad.name, target_element._element, target_pad and target_pad.name, caps)

    def link_pads(self, pad: Pad, target_element: 'Element', target_pad: Pad):
        return self._element.link_pads(pad and pad.name, target_element._element, target_pad and target_pad.name)

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


class Pipeline(YAMLObject):
    yaml_dumper = Dumper
    yaml_loader = Loader

    yaml_tag = u'!Pipeline'

    def __init__(self, pipeline):
        self._pipeline = pipeline

    def add(self, element):
        self._pipeline.add(element.get_element())

    def set_state(self, state):
        return self._pipeline.set_state(state)

    def get_bus(self):
        return self._pipeline.get_bus()

    def dump_dot_graph(self):
        environment_var_name = 'GST_DEBUG_DUMP_DOT_DIR'
        if environment_var_name not in os.environ:
            os.environ[environment_var_name] = "./dots"

        Gst.debug_bin_to_dot_file(self._pipeline, Gst.DebugGraphDetails.ALL, "YAML")

        print(f"- Pipeline debug info written to file '{os.environ[environment_var_name]}/YAML.dot'")


    @classmethod
    def from_yaml(cls, loader, node):
        pipeline = cls(Gst.Pipeline.new("yaml_pipeline"))
        pipeline_map = loader.construct_mapping(node, deep=True)
        
        for element in pipeline_map['elements']:
            pipeline.add(element)

        for link in pipeline_map['links']:
            pre_left = None
            for left, right in zip(link[:-1], link[1:]):
                if isinstance(right, str):
                    pre_left = left
                else:
                    caps, left = (Gst.Caps.from_string(left), pre_left) if isinstance(left, str) else (None, left)
                    left_element, left_pad = (left.element, left) if isinstance(left, Pad) else (left, None)
                    right_element, right_pad = (right.element, right) if isinstance(right, Pad) else (right, None)

                    joiner.join(left_element, left_pad, caps, right_element, right_pad)
                    pre_left = None

        return pipeline

    @classmethod
    def to_yaml(cls, dumper, data):
        return None


ELEMENT_CLASS = Element.build_element_classes()


def load(stream, Loader=Loader):
    pipeline = yaml_load(stream, Loader=Loader)
    return pipeline
