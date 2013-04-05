import functools

import fin.cache
import fin.module


def proxy_fn(name, wrap_fn=None):
    def wrapper(self, *args, **kwargs):
        return self._runner.evaluate("%s.%s(*%r, **%r)" % (self._MODULE_NAME, name, args, kwargs))
    wrapper.__doc__ = getattr(wrap_fn, "__doc__", None)
    return wrapper


class Library(object):

    _MODULE_NAME = NotImplemented
    _PROXY_FUNCS = []
    _PROXY_FUNCS_LOADED = False

    @classmethod
    def LOAD_FUNCS(cls):
        mod = fin.module.import_module_by_name_parts(*cls._MODULE_NAME.split("."))
        if cls._PROXY_FUNCS_LOADED:
            return
        for func_name in cls._PROXY_FUNCS:
            func = proxy_fn(func_name, wrap_fn=getattr(mod, func_name, None))
            setattr(cls, func_name, func)
        cls._PROXY_FUNCS_LOADED = True

    def __init__(self, ssh):
        self._ssh = ssh

    @fin.cache.property
    def _runner(self):
        self._ssh.python.execute("import %s" % self._MODULE_NAME)
        return self._ssh.python