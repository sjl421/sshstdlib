import functools
import os
import shutil
import stat

import sshstdlib.client
import sshstdlib.library


def _auto_remote(fun):
    @functools.wraps(fun)
    def wrap(self, *args, **kwargs):
        if any([isinstance(a, Shutil.Local) for a in (args + tuple(kwargs.values()))]):
            return fun(self, *args, **kwargs)
        return self._runner.evaluate("shutil.%s(*%r, **%r)" 
                                     % (fun.__name__, args, kwargs))
    return wrap


class Shutil(sshstdlib.library.Library):

    __doc__ = shutil.__doc__
    _MODULE_NAME = "shutil"

    class Local(str): 
        """:obj:`str` subclass, passing :samp:`Local("{/path/to/..}")` to any shutil function
        will make it read the path from the local filesystem
        """
        pass

    def _get_os(self, path):
        if isinstance(path, self.Local):
            return os
        return self._ssh.os

    @functools.wraps(shutil.copyfileobj)
    def copyfileobj(self, *args, **kwargs):
        return shutil.copyfileobj(*args, **kwargs)

    @functools.wraps(shutil.copyfile)
    @_auto_remote
    def copyfile(self, src, dst):
        if isinstance(src, self.Local):
            if isinstance(dst, self.Local):
                return shutil.copyfile(src, dst)
            else:
                return self._ssh.sftp.put(src, dst)
        else:
            return self._ssh.sftp.get(src, dst)

    @functools.wraps(shutil.copymode)
    @_auto_remote
    def copymode(self, src, dst):
        src_stat = self._get_os(src).stat(src)
        self._get_os(dst).chmod(dst, src_stat.st_mode)

    @functools.wraps(shutil.copystat)
    @_auto_remote
    def copystat(self, src, dst):
        src_stat = self._get_os(src).stat(src)
        dst_os = self._get_os(dst)
        self.copyfile(src, dst)
        dst_os.chmod(dst, src_stat.st_mode)
        dst_os.utime(dst, (src_stat.st_atime, src_stat.st_mtime))
        if hasattr(src_stat, "st_flags"):
            dst_os.chflags(dst, src_stat.st_flags)

    @functools.wraps(shutil.copy)
    @_auto_remote
    def copy(self, src, dst):
        src_os = self._get_os(src)
        dst_os = self._get_os(dst)
        if dst_os.path.isdir(dst):
            dst = dst_os.path.join(dst, src_os.path.basename(src))
        self.copyfile(src, dst)
        self.copymode(src, dst)
        return dst

    @functools.wraps(shutil.copy2)
    @_auto_remote
    def copy2(self, src, dst):
        dst = self.copy(src, dst)
        self.copystat(src, dst)

    ignore_patterns = shutil.ignore_patterns

    @_auto_remote
    def copytree(self, src, dst, symlinks=False):
        """ Emulates shutil.copytree, but doesn't implement the :obj:`ignore` callback"""
        src_os = self._get_os(src)
        tag_src = type(src)
        dst_os = self._get_os(dst)
        tag_dst = type(dst)
        
        dst_os.mkdir(dst)
        for child in src_os.listdir(src):
            child_path = tag_src(os.path.join(src, child))
            target_path = tag_dst(os.path.join(dst, child))
            info = src_os.stat(child_path)
            if stat.S_ISDIR(info.st_mode):
                self.copytree(child_path, target_path)
            elif stat.S_ISLNK(info.st_mode) and symlinks:
                target = src_os.readlink(child_path)
                dst_os.symlink(target, target_path)
            elif stat.S_ISREG(info.st_mode):
                self.copystat(child_path, target_path)
            else:
                pass # Block/char device