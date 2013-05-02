import StringIO
import pwd
import os
import socket
import subprocess
import sys
import threading
import time
import Queue

import fin.testing
import paramiko.server
import paramiko.sftp_server

import sshstdlib.client


class IgnorePolicy(object):

    def missing_host_key(self, *args, **kwargs):
        return


class ServerBasedTest(fin.testing.TestCase):

    SSH_SERVER_PORT = 8845

    def setUp(self):
        testing_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "testing"))
        key_file = os.path.join(testing_root, "lsh_key")
        seed_file = os.path.join(testing_root, "yarrow_seed")
        os.chmod(seed_file, 0600)
        dummy_askpass = os.path.join(testing_root, "dummy_askpass")
        env = os.environ.copy()
        env["LSH_YARROW_SEED_FILE"] = seed_file
        assert not os.path.exists("%s.lock" % seed_file), "Lock file exists, something went wrong"
        self._server = subprocess.Popen([
            "/usr/sbin/lshd", "-h", key_file, "-q",
            "--interface=127.0.0.1:%s" % self.SSH_SERVER_PORT,
            "--no-publickey",
            "--subsystems=sftp=/usr/lib/lsh-server/sftp-server",
            "--password-helper=%s" % dummy_askpass,
            "--log-file=/dev/stderr"
            ], env=env, close_fds=True)
        self.ssh = paramiko.client.SSHClient()
        self.ssh.set_missing_host_key_policy(IgnorePolicy())

    @fin.cache.property
    def client(self):
        total_sleep = 100
        while total_sleep:
            assert self._server.returncode is None
            try:
                sock = socket.create_connection(("127.0.0.1", self.SSH_SERVER_PORT))
            except Exception, e:
                total_sleep -= 1
                time.sleep(0.05)
            else:
                sock.close()
                break
        assert total_sleep > 0, "Timeout waiting for ssh to start"
        try:
            current_user = os.getlogin()
        except OSError:
            current_user = pwd.getpwuid(os.geteuid()).pw_name
        self.ssh.connect("127.0.0.1", port=self.SSH_SERVER_PORT, username=current_user, 
                         password="none", allow_agent=False, look_for_keys=False)
        client = sshstdlib.client.Client(self.ssh.get_transport())
        client.timeout = None
        return client

    def tearDown(self):
        self.ssh.close()
        self._server.kill()
        self._server.wait()
