import os
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


def set_property(element, key, value):
    """Set element's property
    :param element: Element to set
    :param key: Property name
    :param value: Property value
    :return: None
    """
    if isinstance(value, str):
        value = os.path.expandvars(value)
    print(f"\t{key} as {value}")
    element.set_property(
        key,
        value
    )


def set_properties(element, attributes):
    """Set element properties from a map of attributes"""
    for key, value in attributes.items():
        if isinstance(value, dict):
            pad_template = element.get_pad_template(key)
            if pad_template:
                pad = element.request_pad(pad_template, None, None)
                for pad_key, pad_value in value:
                    set_property(pad, pad_key, pad_value)
        else:
            set_property(element, key, value)


class Element(YAMLObject):
    yaml_dumper = Dumper
    yaml_loader = Loader

    yaml_tag = None
    element_name = None

    @classmethod
    def from_yaml(cls, loader, node):
        element = Gst.ElementFactory.make(cls.element_name, node.anchor)
        print(f"Creating element {cls.element_name} as {node.anchor}")

        assert element is not None, f"cls.element_name: {cls.element_name}"

        if isinstance(node, ScalarNode):
            pass
        elif isinstance(node, MappingNode):
            attributes = loader.construct_mapping(node, deep=True)
            set_properties(element, attributes)

        element.connect('pad-added', on_pad_added)

        return element

    @classmethod
    def to_yaml(cls, dumper, data):
        return None


class Pad(YAMLObject):
    yaml_dumper = Dumper
    yaml_loader = Loader

    yaml_tag = u'!Pad'

    @classmethod
    def from_yaml(cls, loader, node):
        pad_args = loader.construct_sequence(node, deep=True)
        return tuple(pad_args)


class Pipeline(YAMLObject):
    yaml_dumper = Dumper
    yaml_loader = Loader

    yaml_tag = u'!Pipeline'

    @classmethod
    def from_yaml(cls, loader, node):
        pipeline = Gst.Pipeline.new("yaml_pipeline")
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
                    left_element, left_pad, *left_pad_setup = left if isinstance(left, tuple) else (left, None)
                    right_element, right_pad, *right_pad_setup = right if isinstance(right, tuple) else (right, None)

                    joiner.join(left_element, left_pad, caps, right_element, right_pad)
                    pre_left = None

        return pipeline

    @classmethod
    def to_yaml(cls, dumper, data):
        return None


def _build_element_classes(elements):
    element_class = {}
    for element in elements:
        element_class[element] = type(element, (Element,), {
            'yaml_tag': f'!{element}',
            'element_name': f'{element}',
        })
    return element_class


def _get_elements():
    Gst.init()
    reg = Gst.Registry.get()
    return [f.get_name() for f in reg.get_feature_list(Gst.ElementFactory)]


ELEMENT_CLASS = _build_element_classes(_get_elements())


def dump_dot_graph(pipeline):
    environment_var_name = 'GST_DEBUG_DUMP_DOT_DIR'
    if environment_var_name not in os.environ:
        os.environ[environment_var_name] = "./dots"

    Gst.debug_bin_to_dot_file(pipeline, Gst.DebugGraphDetails.ALL, "YAML")

    print(f"- Pipeline debug info written to file '{os.environ[environment_var_name]}/YAML.dot'")


def load(stream, Loader=Loader):
    pipeline = yaml_load(stream, Loader=Loader)
    return pipeline
