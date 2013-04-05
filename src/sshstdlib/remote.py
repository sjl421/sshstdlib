import cPickle as pickle
import sys

import fin

import sshstdlib.remote_client


class RemotePython(object):

    def __init__(self, ssh):
        self.running = False
        self._ssh = ssh

    @fin.cache.property
    def client(self):
        with open(sshstdlib.remote_client.__file__, "rb") as fh:
            client_code = fh.read()
        tempfile = self._ssh.check_call("tempfile").strip()
        self._ssh.check_call("/bin/cat", ">", tempfile, stdin=client_code, shell=True)
        return self._ssh.Popen("/usr/bin/python", "-u", tempfile)

    def _send_command(self, code, payload):
        assert len(code) == 1
        payload_len = str(len(payload))
        data = "%s%s%s%s" % (code, chr(len(payload_len)), payload_len, payload)
        self.client.write(data)

    def _get_bytes(self, num):
        if num == 0:
            return ""
        try:
            data = self.client.read_exact(num)
            assert len(data) == num
            return data
        except:
            if self.client.closed:
                sys.stderr.write(self.client.get_stderr())
            raise

    def _read_result(self):
        result_code, length_length = self._get_bytes(2)
        length = int(self._get_bytes(ord(length_length)))
        payload = pickle.loads(self._get_bytes(length))
        if result_code == "e":
            exc, tb = payload
            exc.remote_traceback = tb
            raise exc
        elif result_code == "o":
            if length > 0:
                return payload

    def evaluate(self, code):
        self._send_command("v", code)
        return self._read_result()

    def execute(self, code):
        self._send_command("x", code)
        self._read_result()

    def reset_context(self):
        self._send_command("r", "")
        self._read_result()

    def stop(self):
        self._send_command("q", "")

    close = stop
