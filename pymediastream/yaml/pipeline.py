import os
from ruamel.yaml import Loader, Dumper, YAMLObject
from gi.repository import Gst
from .pad import Pad
from .joiner import joiner


class Pipeline(YAMLObject):
    yaml_dumper = Dumper
    yaml_loader = Loader

    yaml_tag = u'!Pipeline'

    def __init__(self, pipeline):
        self._pipeline = pipeline
        self._transitions = {}

    def add(self, element):
        self._pipeline.add(element.get_element())

    def get(self, ref):
        element_name, *pad_name = ref.split(':')
        element = self._pipeline.get_by_name(element_name)
        return element.get_static_pad(pad_name[0]) if pad_name else element

    def set_state(self, state):
        return self._pipeline.set_state(state)

    def get_bus(self):
        return self._pipeline.get_bus()

    def dump_dot_graph(self):
        environment_var_name = 'GST_DEBUG_DUMP_DOT_DIR'
        if environment_var_name not in os.environ:
            os.environ[environment_var_name] = "./dots"
        target_dot_file = f'{os.environ[environment_var_name]}/YAML.dot'

        Gst.debug_bin_to_dot_file(self._pipeline, Gst.DebugGraphDetails.ALL, "YAML")

        print(f"- Pipeline debug info written to file '{target_dot_file}'")
        return target_dot_file

    def list_transitions(self):
        return self._transitions.keys()

    def change_to(self, transition_name):
        transition = self._transitions[transition_name]
        transition.run(self)

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

        pipeline._transitions = pipeline_map['transitions']

        return pipeline
