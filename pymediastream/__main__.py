import threading
import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
from gst_yaml import load, dump_dot_graph
from shell import StreamControllerShell


def bus_call(_bus, message, loop):
    t = message.type
    if t == Gst.MessageType.EOS:
        sys.stdout.write("End-of-stream\n")
        loop.quit()
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        sys.stderr.write("Error: %s: %s\n" % (err, debug))
        loop.quit()
    return True


def shell_loop(pipeline):
    StreamControllerShell(pipeline, Gst.State.PAUSED).cmdloop("Starting")


def main(args):
    if len(args) != 2:
        sys.stderr.write("usage: %s <media file or uri>\n" % args[0])
        sys.exit(1)

    Gst.init(None)

    with open(args[1], 'r') as descriptor:
        pipeline = load(descriptor)

    pipeline.set_state(Gst.State.PAUSED)

    dump_dot_graph(pipeline)

    loop = GLib.MainLoop()

    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    thread = threading.Thread(target=shell_loop, args=(pipeline,))
    thread.daemon = True
    thread.start()

    loop.run()

    thread.join()

    pipeline.set_state(Gst.State.NULL)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
