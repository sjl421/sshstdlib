import subprocess
import collections
import os
import posix
import sys
import itertools

import fin.cache
import json

import sshstdlib.library

proxy = sshstdlib.library.proxy_fn


class RemoteEnviron(collections.MutableMapping):

    def __init__(self, runner):
        self._runner = runner

    def __delitem__(self, name):
        return self._runner.execute("del os.environ[%r]" % name)

    def __setitem__(self, name, value):
        return self._runner.execute("os.environ[%r] = %r" % (name, value))

    def __getitem__(self, name):
        return self._runner.evaluate("os.environ[%r]" % (name, ))

    def __contains__(self, name):
        return self._runner.evaluate("%r in os.environ" % (name, ))

    def __iter__(self):
        return iter(self._runner.evaluate("os.environ.keys()"))

    def __len__(self):
        return len(self._runner.evaluate("len(os.environ)"))


class OS(sshstdlib.library.Library):

    _MODULE_NAME = "os"
    _PROXY_FUNCS = [
        "access",
        "chdir",
        "chdir",
        "chflags",
        "chmod",
        "chown",
        "chroot",
        "close",
        "dup",
        "dup2",
        "fchdir",
        "fchmod",
        "fchown",
        "fdatasync",
        "fpathconf",
        "fstat",
        "fstatvfs",
        "fsync",
        "ftruncate",
        "getcwd",
        "getegid",
        "geteuid",
        "getgid",
        "getgroups",
        "getlogin",
        "getuid",
        "isatty",
        "lchflags",
        "lchown",
        "link",
        "listdir",
        "lseek",
        "lstat",
        "makedirs",
        "mkdir",
        "mkfifo",
        "open",
        "openpty",
        "pathconf",
        "pipe",
        "readnames",
        "read",
        "readlink",
        "remove",
        "removedirs",
        "rename",
        "renames",
        "rmdir",
        "stat",
        "strerror",
        "tcgetpgrp",
        "ttyname",
        "umask",
        "uname",
        "unlink",
        "utime",
        "write",
    ]

    class error(os.error): pass

    @property
    def name(self):
        return self._runner.evaluate("os.name")

    @fin.cache.property
    def environ(self):
        return RemoteEnviron(self._runner)

    @fin.cache.property
    def path(self):
        return Path(self._ssh)

OS.LOAD_FUNCS()

class Path(sshstdlib.library.Library):

    _MODULE_NAME = "os.path"
    _PROXY_FUNCS = [
        "abspath",
        "basename",
        "commonprefix",
        "dirname",
        "exists",
        "lexists",
        "expanduser",
        "expandvars",
        "getatime",
        "getmtime",
        "getctime",
        "getsize",
        "isabs",
        "isfile",
        "isdir",
        "islink",
        "ismount",
        "normcase",
        "normpath",
        "realpath",
        "split",
        "splitdrive",
        "splitext",
        "splitunc",
        "join",
        "relpath",
    ]

    @property
    def supports_unicode_filenames(self, *parts):
        return self._ssh.run_python("import os.path; out=os.path.supports_unicode_filenames")

Path.LOAD_FUNCS()