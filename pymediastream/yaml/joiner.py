
class Joiner:
    """ This class support lazy element joiner """
    def __init__(self):
        self._lazy_join = {}

    def join(self, left_element, left_pad, caps, right_element, right_pad):
        left_pad = left_pad or left_element.get_unlinked_srcpad()
        right_pad = right_pad or right_element.get_unlinked_sinkpad()

        if caps:
            result = left_element.link_pads_filtered(left_pad, right_element, right_pad, caps)
            print(f"Linked {result}: {left_element.name}:{left_pad and left_pad.name}"
                  f" -[{caps.to_string()}]-> "
                  f"{right_element.name}:{right_pad and right_pad.name}")
        else:
            result = left_element.link_pads(left_pad, right_element, right_pad)
            print(f"Linked {result}: {left_element.name}:{left_pad and left_pad.name}"
                  f" --> "
                  f"{right_element.name}:{right_pad and right_pad.name}")

        if result is False:
            ref = f"{left_element.name}:{left_pad.name}"
            print(f"Creating lazy join {ref}")
            self._lazy_join[ref] = (
                left_element,
                left_pad,
                caps,
                right_element,
                right_pad
            )

    def __contains__(self, item):
        return item in self._lazy_join

    def join_lazy(self, ref):
        print(f"Joining lazy {ref}")
        self.join(*self._lazy_join[ref])
        pass


joiner = Joiner()