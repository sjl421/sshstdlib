import cPickle as pickle
import os
import sys
import traceback


_OBJECT_CACHE = {}


def RemoteProxy(name, id):
    return _OBJECT_CACHE[id]


def restore_globals(context):
    context["_OBJECT_CACHE"] = _OBJECT_CACHE
    context["RemoteProxy"] = RemoteProxy


def read_exact(n):
    remaining = n
    all_data = ""
    while remaining:
        data = sys.stdin.read(remaining)
        if data == '':
            raise SyntaxError("Unexpected EOF while parsing")
        remaining -= len(data)
        all_data += data
        assert remaining >= 0
    return all_data


def send(code, data):
    assert len(code) == 1
    data = pickle.dumps(data)
    length = str(len(data))
    sys.stdout.write(code + chr(len(length)) + length)
    sys.stdout.write(data)


def main(args):
    if "remove_source" in args:
        os.unlink(__file__)
    context = {}
    while True:
        restore_globals(context)
        action, length_length = read_exact(2)
        length = int(read_exact(ord(length_length)))
        payload = read_exact(length)
        if action == "v":
            try:
                send("o", eval(payload, context))
            except Exception, e:
                send("e", (e, traceback.format_exc()))
        elif action == "x":
            try:
                exec payload in context
            except Exception, e:
                send("e", (e, traceback.format_exc()))
            else:
                send("o", None)
        elif action == "r":
            context = {}
            send("o", None)
        elif action == "q":
            return


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
