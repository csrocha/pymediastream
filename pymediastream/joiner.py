def next_unlinked(pads):
    """ Select first unlinked pad in a list """
    return next((pad.name for pad in pads if not pad.is_linked()), None)


class Joiner:
    """ This class support lazy element joiner """
    def __init__(self):
        self._lazy_join = {}

    def join(self, left_element, left_pad, caps, right_element, right_pad):
        left_pad = left_pad or next_unlinked(left_element.srcpads)
        right_pad = right_pad or next_unlinked(right_element.sinkpads)

        if caps:
            result = left_element.link_pads_filtered(left_pad, right_element, right_pad, caps)
            print(f"Linked {result}: {left_element.name}:{left_pad}"
                  f" -[{caps.to_string()}]-> "
                  f"{right_element.name}:{right_pad}")
        else:
            result = left_element.link_pads(left_pad, right_element, right_pad)
            print(f"Linked {result}: {left_element.name}:{left_pad}"
                  f" --> "
                  f"{right_element.name}:{right_pad}")

        if result is False:
            self._lazy_join[f"{left_element.name}:{left_pad}"] = (left_element, left_pad,
                                                                  caps,
                                                                  right_element, right_pad)

    def __contains__(self, item):
        return item in self._lazy_join

    def join_lazy(self, ref):
        print(f"Joining lazy {ref}")
        self.join(*self._lazy_join[ref])
        pass
