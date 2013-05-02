import subprocess

import sshstdlib.library as library


class RemoteFile(library.RemoteObject):
    
    closed = library.remote_property("closed")
    encoding = library.remote_property("encoding")
    errors = library.remote_property("errors")
    mode = library.remote_property("mode")
    name = library.remote_property("name")
    newlines = library.remote_property("newlines")
    softspace = library.remote_property("softspace")


RemoteFile._LOAD_PROXY(file)


class Popen(library.RemoteObject):
    
    stdin = library.remote_property("stdin", cache=RemoteFile)
    stdout = library.remote_property("stdout", cache=RemoteFile)
    stderr = library.remote_property("stderr", cache=RemoteFile)
    
    pid = library.remote_property("pid")
    returncode = library.remote_property("returncode")
    
    def communicate_into(self, stdin_var, stderr_var, input=None):
        """Like Response.read, but stores the result in the remote variable ``dest``"""
        library.check_valid_name(stdin_var)
        library.check_valid_name(stderr_var)
        self._ssh.python.execute("%s, %s=%r.communicate(%r)" 
                                 % (stdin_var, stderr_var, input))


Popen._LOAD_PROXY(subprocess.Popen)


class Subprocess(library.Library):

    _MODULE_NAME = "subprocess"
    _PROXY_FUNCS = ["call", "check_call", "check_output"]

    PIPE = subprocess.PIPE  # This relies on the value of PIPE not changing
    STDOUT = subprocess.STDOUT  # This relies on the value of STDOUT not changing

    Popen = library.cached_object("Popen", Popen, wraps=subprocess.Popen)


Subprocess.LOAD_FUNCS()
