try:
    import cStringIO as StringIO
except ImportError:
    import StringIO  # NOQA

import json
import os
import sys
import socket
import subprocess

import paramiko.client

import fin.cache
import sshstdlib.remote
import sshstdlib.sshos
import sshstdlib.exec_channel


class _IgnorePolicy(object):

    def missing_host_key(self, *args, **kwargs):
        return


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
    # Derived from: http://stackoverflow.com/questions/990758/reclassing-an-instance-in-python
    class SFTPFile(file_ob.__class__):

        def __enter__(self):
            return self

        def __exit__(self, *args, **kwargs):
            self.close()
    file_ob.__class__ = SFTPFile
    return file_ob


class Client(object):

    """A simplified SSH Client interface, with a focus on successfully
        connecting within a trusted environment, loosely based on paramiko.SSHClient

        :param transport: A valid Transport object (usually obtained by calling 
                          `get_tranport` on a connected paramiko client object)
        :type transport: :py:class:`paramiko.transport.Transport`
        :param timeout: If not :keyword:`None`, establishes a secondary channel to monitor the 
                        ssh connection.  
                        If a remote call blocks for timeout seconds, a heartbeat is sent over 
                        the secondary channel, 
                        if the heartbeat doesn't return within timeout seconds, raises an exception.
        :type timeout: int / :keyword:`None`
    """

    def __init__(self, transport, timeout=1):
        self.transport = transport
        self._timeout = timeout
        self.timeout = timeout

    @classmethod
    def connect(cls, *args, **kwargs):
        """Set up an SSH session, and bind it to the client.
            All arguments (except :py:obj:`no_keys`) are passed directly 
            to :py:meth:`paramiko.client.SSHClient.connect`

            :param hostname: The server to connect to
            :type hostname: str
            :param port: The server port to connect to (default=22)
            :type port: int
            :param username: the username to authenticate as (defaults to the
                             current local username)
            :type username: str
            :param password: a password to use for authentication or for unlocking
                             a private key
            :type password: str
            :param pkey: an optional private key to use for authentication
            :type pkey: :py:class:`paramiko.pkey.PKey`
            :param others: See paramiko documentation
            :type others: kwargs
            :rtype: :class:`Client`
        """
        ssh = paramiko.client.SSHClient()
        no_keys = False
        if "no_keys" in kwargs:
            no_keys = kwargs.pop("no_keys")
        if no_keys:
            ssh.set_missing_host_key_policy(_IgnorePolicy())
        else:
            ssh.load_system_host_keys()
        ssh.connect(*args, **kwargs)
        instance = cls(ssh.get_transport())
        instance._referenced_ssh = ssh
        return instance

    @property
    def timeout(self):
        return self._timeout
    
    @timeout.setter  # NOQA
    def timeout(self, value):
        self._timeout = value
        if value is None:
            cls = type(self)
            if cls._ping_channel.has_cached(self):
                self._ping_channel.close()
                cls._ping_channel.reset(self)
        else:
            _ = self._ping_channel  # NOQA

    def Popen(self, cmd, *args, **kwargs):
        """Loosely modelled on the subprocess.Popen interface. 
            Runs `cmd [args...]` on remote machine.  The returned object
            can be read from, written to, and has some methods that are a bit
            similar to the standard Popen object.

            :param cmd: the executable to run
            :type cmd: str
            :param \*args: string arguments to pass to cmd
            :type cmd: list of strings
            :param shell: (Default: :py:obj:`False`) call the command from 
                          a new :command:`/bin/bash` instance.
            :type shell: :py:class:`bool`
            :param env: (Default: :py:obj:`{}`) Set all items in `env` as environment variables.
                        *Note*: this inlines all variables using env KEY=VALUE KEY2=VALUE2... 
                        so this may cause issues on some systems that have limits.
            :type env: :py:class:`dict`
            :rtype: :class:`sshstdlib.exec_channel.ExecChannel`
            """
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
        marker = None
        if shell:
            marker = "__sshstdlib start__"
            cmd = "bash -lc 'echo -n %s;%s'" % (marker, cmd, )
        if env is not None:
            cmd = "%s %s" % (make_env_cmd(env), cmd)
        
        channel = sshstdlib.exec_channel.ExecChannel(self)
        channel.start(cmd, marker=marker)
        return channel
        
    def check_call(self, cmd, *args, **kwargs):
        stdin = ""
        expect_json = False
        silent = False
        if "silent" in kwargs:
            silent = kwargs.pop("silent")
        if "expect_json" in kwargs:
            expect_json = kwargs.pop("expect_json")
        if "stdin" in kwargs:
            stdin = kwargs.pop("stdin")

        with self.Popen(cmd, *args, **kwargs) as exe:
            exit_code, stdout, stderr = exe.communicate(stdin)

        if not silent:
            sys.stderr.write(stderr)
        if exit_code != 0:
            raise CalledProcessError(exit_code, cmd)
        if expect_json:
            return json.loads(stdout)
        return stdout

    @property
    def active(self):
        return self.transport.is_active()

    def ping(self):
        if not self.active:
            return False
        if self.timeout is None:
            return True
        try:
            self._ping_channel.write("ping\n")
            data = self._ping_channel.read_exact(5)
            assert data == "ping\n", "Received unexpected ping reply: %r" % (data, )
        except socket.timeout:
            return False
        return True

    @fin.cache.property
    def os(self):
        """ Emulated os module - :class:`sshstdlib.sshos.OS` """
        return sshstdlib.sshos.OS(self)

    @fin.cache.property
    def shutil(self):
        """ Emulated shutil module - :class:`sshstdlib.sshshutil.Shutil` """
        import sshstdlib.sshshutil
        return sshstdlib.sshshutil.Shutil(self)

    @fin.cache.property
    def tempfile(self):
        """ Emulated tempfile module - :class:`sshstdlib.sshtempfile.TempFile` """
        import sshstdlib.sshtempfile
        return sshstdlib.sshtempfile.TempFile(self)

    @fin.cache.property
    def urllib2(self):
        """ Emulated urllib2 module - :class:`sshstdlib.sshurllib2.Urllib2` """
        import sshstdlib.sshurllib2
        return sshstdlib.sshurllib2.Urllib2(self)

    @fin.cache.property
    def subprocess(self):
        """ Emulated subprocess module - :class:`sshstdlib.sshsubprocess.Subprocess` """
        import sshstdlib.sshsubprocess
        return sshstdlib.sshsubprocess.Subprocess(self)

    @fin.cache.property
    def sftp(self):
        """An opened paramiko sftp channel (created on first use). Intended for internal use"""
        return self.transport.open_sftp_client()

    @fin.cache.property
    def python(self):
        """A :class:`sshstdlib.remote.RemotePython` instance (created on first use). 
           Intended for internal use"""
        return sshstdlib.remote.RemotePython(self)

    @fin.cache.property
    def _ping_channel(self):
        """An object that can be used to check if a connection is still 'alive'."""
        channel = sshstdlib.exec_channel.ExecChannel(self, _direct=True)
        channel.start("cat")
        return channel

    def open(self, name, mode="rb"):
        """Similar to the :obj:`open` builtin"""
        return add_contextmanager(self.sftp.open(name, mode=mode))
