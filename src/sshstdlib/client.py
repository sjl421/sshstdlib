try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

import json
import os
import sys
import socket
import subprocess

import fin.cache
import sshstdlib.remote
import sshstdlib.sshos
import sshstdlib.exec_channel


class CalledProcessError(subprocess.CalledProcessError): 
    pass


class ConnectionDead(Exception): 
    pass


def make_env_cmd(env):    
    parts = tuple(("%s=%s" % (k, v) for k, v in env.iteritems()))
    return subprocess.list2cmdline(("env", ) + parts)


def get_python_cmd():
    # There may be better ways of doing this? Ideally return version-specific
    # python as often as possible (i.e. python2.7)
    return os.path.basename(sys.executable)


def add_contextmanager(file_ob):
    # Approach taken from: http://stackoverflow.com/questions/990758/reclassing-an-instance-in-python
    class SFTPFile(file_ob.__class__):

        def __enter__(self):
            return self

        def __exit__(self, *args, **kwargs):
            self.close()
    file_ob.__class__ = SFTPFile
    return file_ob


class Client(object):

    """A simplified SSH Client interface, with a focus on successfully
        connecting within a trusted environment, loosely based on paramiko.SSHCLient"""

    def __init__(self, transport, timeout=1):
        self.transport = transport
        self.timeout = timeout    

    def Popen(self, cmd, *args, **kwargs):
        shell = False
        env = None
        if "shell" in kwargs:
            shell = kwargs.pop("shell")
        if "env" in kwargs:
            env = kwargs.pop("env")

        if len(kwargs) > 0:
            raise TypeError("Popen() got unexpected keyword argument '%s'" 
                            % (kwargs.keys()[0], ))
        
        cmd = subprocess.list2cmdline((cmd, ) + args)

        if shell:
            cmd = "bash -c '%s'" % (cmd, )
        if env is not None:
            cmd = "%s %s" % (make_env_cmd(env), cmd)
        
        channel = sshstdlib.exec_channel.ExecChannel(self)
        channel.start(cmd)
        return channel
        
    def check_call(self, cmd, *args, **kwargs):
        stdin = ""
        expect_json = False
        if "expect_json" in kwargs:
            expect_json = kwargs.pop("expect_json")
        if "stdin" in kwargs:
            stdin = kwargs.pop("stdin")

        with self.Popen(cmd, *args, **kwargs) as exe:
            exit_code, stdout, stderr = exe.communicate(stdin)

        sys.stderr.write(stderr)
        if exit_code != 0:
            raise CalledProcessError(exit_code, cmd)
        if expect_json:
            return json.loads(stdout)
        return stdout

    @fin.cache.property
    def os(self):
        return sshstdlib.sshos.OS(self)

    @fin.cache.property
    def shutil(self):
        import sshstdlib.sshshutil
        return sshstdlib.sshshutil.Shutil(self)

    @fin.cache.property
    def tempfile(self):
        import sshstdlib.sshtempfile
        return sshstdlib.sshtempfile.TempFile(self)

    @fin.cache.property
    def sftp(self):
        return self.transport.open_sftp_client()

    @fin.cache.property
    def python(self):
        return sshstdlib.remote.RemotePython(self)

    def open(self, name, mode="rb"):
        return add_contextmanager(self.sftp.open(name, mode=mode))