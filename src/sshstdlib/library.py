import fin.cache

def proxy_fn(name):
    def wrapper(self, *args, **kwargs):
        return self._runner.evaluate("%s.%s(*%r, **%r)" % (self._MODULE_NAME, name, args, kwargs))
    return wrapper


class Library(object):

    _MODULE_NAME = NotImplemented
    _PROXY_FUNCS = []
    _PROXY_FUNCS_LOADED = False

    @classmethod
    def load_funcs(cls):
        if cls._PROXY_FUNCS_LOADED:
            return
        for func_name in cls._PROXY_FUNCS:
            setattr(cls, func_name, proxy_fn(func_name))
        cls._PROXY_FUNCS_LOADED = True

    def __init__(self, ssh):
        self._ssh = ssh
        self.load_funcs()

    @fin.cache.property
    def _runner(self):
        self._ssh.python.execute("import %s" % self._MODULE_NAME)
        return self._ssh.python