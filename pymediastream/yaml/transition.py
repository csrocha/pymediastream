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
        prev_state = pipeline._pipeline.current_state
        pipeline.set_state(Gst.State.NULL)
        for element_name, setup in self._final_state.items():
            element = pipeline.get(element_name)
            element.set_properties(**setup)
        pipeline.set_state(prev_state)

    @classmethod
    def from_yaml(cls, loader, node):
        final_state = loader.construct_mapping(node, deep=True)
        return cls(final_state)
