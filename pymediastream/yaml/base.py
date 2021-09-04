from typing import Any
import os
from yaml.joiner import Joiner

joiner = Joiner()


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
