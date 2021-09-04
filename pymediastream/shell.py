from gi.repository import Gst
import cmd
import graphviz
from pymediastream.gst_yaml import Pipeline


class StreamControllerShell(cmd.Cmd):
    intro = "Stream Controller Shell. Type help or ? to list commands.\n"
    prompt = "(streamer) "

    def __init__(self, pipeline: Pipeline, initial_state):
        self._pipeline = pipeline
        self._initial_state = initial_state
        super().__init__()

    def do_elements(self, arg):
        """List elements."""
        iterable = self._pipeline.iterate_elements()
        while True:
            result, value = iterable.next()
            if result == Gst.IteratorResult.DONE:
                break
            elif result != Gst.IteratorResult.OK:
                raise RuntimeError(result)
            print(value.name)

    def do_stop(self, arg):
        """Play the pipeline or element of the pipeline."""
        self._pipeline.set_state(Gst.State.NULL)

    def do_pause(self, arg):
        """Pause the pipeline or element of the pipeline."""
        self._pipeline.set_state(Gst.State.PAUSED)
        pass

    def do_play(self, arg):
        """Pause the pipeline or element of the pipeline."""
        self._pipeline.set_state(Gst.State.PLAYING)
        pass

    def do_info(self, arg):
        """Show element info."""
        element = self._pipeline.get_by_name(arg) if arg else self._pipeline
        print(f"Name: {element.name}")
        print(f"Duration: {element.query_duration(Gst.Format.TIME).duration/(10**9)} Seg")
        print(f"Position: {element.query_position(Gst.Format.TIME).cur/(10**9)} Seg")
        print("Properties:")
        for p in element.list_properties():
            key = p.name
            value = element.get_property(key)
            print(f"\t{key}: {value}")
        pass

    def do_graph(self, args):
        dot_file = self._pipeline.dump_dot_graph()
        dot_src = graphviz.Source.from_file(dot_file)
        dot_src.render(view=True)

    def do_seek(self, arg):
        if not arg:
            print("Requires element position or only position.")
            return

        first, *second = arg.split(" ", 1)

        element = self._pipeline.get_by_name(first) if second else self._pipeline
        position = second[0] if second else first
        element.seek_simple(Gst.Format.PERCENT, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, float(position)*(10**9))

    def do_set(self, arg):
        element_name, key, value = arg.split(' ', 2)
        element = self._pipeline.get_by_name(element_name) if element_name else self._pipeline
        element.set_property(key, value)

    def do_exit(self, arg):
        """Stop processing."""
        self.close()
        return True

    def do_debug(self, arg):
        """Show element info."""
        import pdb
        pdb.set_trace()

    def preloop(self):
        self._pipeline.set_state(self._initial_state)

    def postloop(self):
        self._pipeline.set_state(Gst.State.NULL)

    def close(self):
        if self._pipeline:
            self._pipeline.set_state(Gst.State.NULL)
