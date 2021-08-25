import os
from ruamel.yaml import load as yaml_load
from ruamel.yaml import Loader, Dumper, YAMLObject
from ruamel.yaml import ScalarNode, MappingNode
from gi.repository import Gst


def on_pad_added(*args):
    return True


def set_property(element, key, value):
    if isinstance(value, str):
        value = os.path.expandvars(value)
    print(f"\t{key} as {value}")
    element.set_property(
        key,
        value
    )


def set_properties(element, attributes):
    for key, value in attributes.items():
        if isinstance(value, dict): # The key reference to a pad
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


def build_element_classes(elements):
    element_class = {}
    for element in elements:
        element_class[element] = type(element, (Element,), {
            'yaml_tag': f'!{element}',
            'element_name': f'{element}',
        })
    return element_class


def get_plugins():
    Gst.init()
    reg = Gst.Registry.get()
    return [p.get_name() for p in reg.get_plugin_list()]


def get_elements():
    Gst.init()
    reg = Gst.Registry.get()
    return [f.get_name() for f in reg.get_feature_list(Gst.ElementFactory)]


ELEMENT_CLASS = build_element_classes(get_elements())


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
            caps = None
            pre_left = None
            for left, right in zip(link[:-1], link[1:]):
                if isinstance(right, str):
                    caps = Gst.Caps.from_string(right)
                    pre_left = left
                elif isinstance(left, str) and caps:
                    result = pre_left.link_filtered(right, caps)
                    print(f"Linked {result}: {pre_left.name} -[{caps.to_string()}]-> {right.name}")
                    caps = None
                    pre_left = None
                elif isinstance(left, tuple):
                    element, pad_name, *pad_setup = left
                    result = element.link_pads(pad_name, right, None)
                    if result and pad_setup:
                        pad = [pad for pad in element.sinkpads if pad.name == pad_name][0]
                        for key, value in pad_setup[0].items():
                            set_property(pad, key, value)
                    print(f"Linked {result}: {element.name}::{pad_name} -> {right.name}")
                    caps = None
                    pre_left = None
                elif isinstance(right, tuple):
                    element, pad_name, *pad_setup = right
                    result = left.link_pads(None, element, pad_name)
                    if result and pad_setup:
                        pad = [pad for pad in element.sinkpads if pad.name == pad_name][0]
                        for key, value in pad_setup[0].items():
                            set_property(pad, key, value)
                    print(f"Linked {result}: {left.name} -> {element.name}::{pad_name}")
                    caps = None
                    pre_left = None
                else:
                    result = left.link(right)
                    print(f"Linked {result}: {left.name} -> {right.name}")
                    caps = None
                    pre_left = None

        return pipeline

    @classmethod
    def to_yaml(cls, dumper, data):
        return None


class Caps(YAMLObject):
    yaml_dumper = Dumper
    yaml_loader = Loader

    yaml_tag = u'!capsfilter'

    @classmethod
    def from_yaml(cls, loader, node):
        caps_string = loader.construct_scalar(node)
        caps = Gst.Caps.from_string(caps_string)
        element = Gst.ElementFactory.make("capsfilter", None)
        element.set_properties("caps", caps)
        return element

    @classmethod
    def to_yaml(cls, dumper, data):
        return None


def dump_dot_graph(pipeline):
    envname = 'GST_DEBUG_DUMP_DOT_DIR'
    if envname not in os.environ:
        os.environ[envname] = "./dots"

    Gst.debug_bin_to_dot_file(pipeline, Gst.DebugGraphDetails.ALL, "YAML")

    print(f"- Pipeline debug info written to file '{os.environ[envname]}/YAML.dot'")


def load(stream, Loader=Loader):
    pipeline = yaml_load(stream, Loader=Loader)
    return pipeline
