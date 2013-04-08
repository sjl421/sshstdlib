import tempfile

import sshstdlib.client
import sshstdlib.library


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


class TempFile(sshstdlib.library.Library):

    __doc__ = tempfile.__doc__
    _MODULE_NAME = "tempfile"
    _PROXY_FUNCS = ["mkstemp", "mkdtemp", "gettempdir"]

    def __init__(self, ssh):
        self._ssh = ssh
        self.tempdir = None

    def NamedTemporaryFile(self, mode="w+b", suffix="", prefix="tmp", dir=None, delete=True):
        fd, path = self.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
        def close():
            self._ssh.os.close(fd)
            self._ssh.os.unlink(path)
        file_ob = self._ssh.open(path, mode=mode)
        return make_delete_on_close(file_ob, path, close)

TempFile.LOAD_FUNCS()