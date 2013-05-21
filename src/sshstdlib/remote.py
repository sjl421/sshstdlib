import cPickle as pickle
import os
import sys

import fin

import sshstdlib.remote_client
import sshstdlib.client


class RemotePython(object):

    def __init__(self, ssh):
        self.running = False
        self._ssh = ssh

    @fin.cache.property
    def client(self):
        client_path = os.path.join(os.path.dirname(__file__), "remote_client.py")
        with open(client_path, "rb") as fh:
            client_code = fh.read()
        try:
            tempfile = self._ssh.check_call("tempfile", silent=True).strip()
        except sshstdlib.client.CalledProcessError:
            tempfile = ""
        if tempfile.strip() == "":
            tempfile = self._ssh.check_call(
                self._executable,
                "-c", "import tempfile; _, p = tempfile.mkstemp(); print p").strip()
        self._ssh.check_call("/bin/cat", ">", tempfile, stdin=client_code, shell=True)
        return self._ssh.Popen(self._executable, "-u", tempfile, "remove_source")

    def _send_command(self, code, payload):
        assert len(code) == 1
        payload_len = str(len(payload))
        data = "%s%s%s%s" % (code, chr(len(payload_len)), payload_len, payload)
        self.client.write(data)

    @fin.cache.property
    def _executable(self):
        candidates = ["python%s.%s" % (sys.version_info[0], sys.version_info[1]),
                      "python%s" % (sys.version_info[0], ),
                      "python"]
        proc = self._ssh.Popen("which", *candidates, shell=True)
        _, stdout, stderr = proc.communicate()
        found = [l.strip() for l in stdout.strip().split("\n")]
        if len(found) == 0:
            # Probably on windows or something
            return "python"
        return found[0]

    @fin.cache.method
    def set_default(self, name, default):
        self.execute("%s=%r" % (name, default))

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
