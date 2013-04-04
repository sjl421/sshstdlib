import collections
import os
import sys
import itertools

import fin.cache
import json

import sshstdlib.client


def make_delete_on_close(file_ob, path, unlink_call):
    class SFTPFile(file_ob.__class__):

        def _close(self, async=False):
            rv = super(SFTPFile, self)._close(async)
            try:
                unlink_call()
            except:
                if not async:
                    raise
            return rv

    file_ob.name = path
    file_ob.__class__ = SFTPFile
    return file_ob


class TempFile(object):

    def __init__(self, ssh):
        self._ssh = ssh
        self.tempdir = None

    def _mkstemp(self, suffix="", prefix="tmp", dir=None, make_directory=False):
        if dir is None:
            dir = self.tempdir
        template = "%sXXXXXX%s" % (prefix, suffix)
        args = ["--tmpdir" if dir is None else "--tmpdir=%s" % dir, template]
        if make_directory:
            args.append("-d")
        return self._ssh.check_call("mktemp", *args).strip()

    def NamedTemporaryFile(self, mode="w+b", suffix="", prefix="tmp", dir=None, delete=True):
        path = self._mkstemp(suffix, prefix, dir)
        unlink_call = lambda: self._ssh.os.unlink(path)
        file_ob = self._ssh.open(path, mode=mode)
        return make_delete_on_close(file_ob, path, unlink_call)

    def mkstemp(self, suffix="", prefix="tmp", dir=None):
        path = self._mkstemp(suffix, prefix, dir)
        file_ob = self._ssh.open(path)
        return file_ob, path

    def mkdtemp(self, suffix="", prefix="tmp", dir=None):
        return self._mkstemp(suffix, prefix, dir, make_directory=True)

    def gettempdir(self):
        if self.tempdir is not None:
            return self.tempdir
        return self._ssh.os.environ.get("TMPDIR", "/tmp")
