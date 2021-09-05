from typing import Dict, Any
from ruamel.yaml import Loader, Dumper, YAMLObject
from gi.repository import Gst
from gst_yaml import Element


class Transition(YAMLObject):
    yaml_dumper = Dumper
    yaml_loader = Loader

    yaml_tag = u'!Transition'

    def __init__(self, final_state: Dict[str, Dict[str, Any]]):
        self._final_state = final_state

    def run(self, pipeline):
        prev_state = {}
        for element_name, setup in self._final_state.items():
            if '_null_reset' in setup:
                element = pipeline.get(element_name)
                prev_state[element_name] = element.current_state
                element.set_state(Gst.State.NULL)

        for element_name, setup in self._final_state.items():
            to_setup = {k:v for k, v in setup.items() if k[0] != '_'}
            if to_setup:
                element = pipeline.get(element_name)
                element.set_properties(**to_setup)

        for element_name, next_state in prev_state.items():
            element = pipeline.get(element_name)
            element.set_state(next_state)

    @classmethod
    def from_yaml(cls, loader, node):
        final_state = loader.construct_mapping(node, deep=True)
        return cls(final_state)
