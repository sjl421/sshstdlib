import collections
import re

import fin.cache
import fin.module


OBJECT_CACHE_NAME = "_OBJECT_CACHE"
VALID_NAME_RE = re.compile("^[a-zA-Z_][a-zA-Z0-9_]*$")


def check_valid_name(name):
    if VALID_NAME_RE.match(name) is None:
        raise AssertionError("'%s' is not a valid python identifier" % (name, ))


class RemoteDict(collections.MutableMapping):

    def __init__(self, runner, name):
        self._runner = runner
        self._name = name

    def __delitem__(self, name):
        return self._runner.execute("del %s[%r]" % (self._name, name))

    def __setitem__(self, name, value):
        return self._runner.execute("%s[%r] = %r" % (self._name, name, value))

    def __getitem__(self, name):
        return self._runner.evaluate("%s[%r]" % (self._name, name, ))

    def __contains__(self, name):
        return self._runner.evaluate("%r in %s" % (name, self._name))

    def __iter__(self):
        return iter(self._runner.evaluate("%s.keys()" % (self._name, )))

    def __len__(self):
        return len(self._runner.evaluate("len(%s)" % (self._name, )))


def library_fn(name, wraps=None):
    def wrapper(self, *args, **kwargs):
        return self._runner.evaluate(
            "%s.%s(*%r, **%r)" % (self._MODULE_NAME, name, args, kwargs))
    wrapper.__doc__ = getattr(wraps, "__doc__", None)
    return wrapper


def cached_object(name, result_class, wraps=None):
    def wrapper(self, *args, **kwargs):
        self._runner.set_default(OBJECT_CACHE_NAME, {})        
        self._runner.execute(
            "result = %s.%s(*%r, **%r); %s[id(result)] = result" 
            % (self._MODULE_NAME, name, args, kwargs, OBJECT_CACHE_NAME))
        return result_class(self._ssh, self._runner.evaluate("id(result)"))
    wrapper.__doc__ = getattr(wraps, "__doc__", None)
    return wrapper


def remote_ob_fn(name, wraps=None):
    def wrapper(self, *args, **kwargs):
        return self._with_object(".%s(*%r, **%r)" % (name, args, kwargs))
    wrapper.__doc__ = getattr(wraps, "__doc__", None)
    return wrapper


def remote_property(name, wraps=None, cache=None):
    if cache is not None:
        def wrapper(self, *args, **kwargs):
            self._ssh.python.set_default(OBJECT_CACHE_NAME, {})
            self._ssh.python.execute(
                "result = %s[%i].%s" % (OBJECT_CACHE_NAME, self._id, name))
            self._ssh.python.execute(
                "%s[id(result)] = result" % (OBJECT_CACHE_NAME, ))
            return cache(self._ssh, self._ssh.python.evaluate("id(result)"))
    else:
        def wrapper(self, *args, **kwargs):  # NOQA
            return self._with_object(".%s" % (name, ))
    wrapper.__doc__ = getattr(wraps, "__doc__", None)
    return property(wrapper)


class RemoteObject(object):
    
    @classmethod
    def _LOAD_PROXY(cls, proxy):
        for name in dir(proxy):
            if (name.startswith("_") and name != "__doc__") or hasattr(cls, name):
                continue
            meth = getattr(proxy, name)
            if not callable(meth):
                setattr(cls, name, meth)
            else:
                setattr(cls, name, remote_ob_fn(name, wraps=meth))

    def __init__(self, ssh, id):
        self._ssh = ssh
        self._id = id

    def _with_object(self, partial):
        return self._ssh.python.evaluate(
            "%s[%i]%s" % (OBJECT_CACHE_NAME, self._id, partial))

    def _discard(self):
        self._ssh.python.execute("%s.pop(%i, None)" % (OBJECT_CACHE_NAME, self._id))

    def __del__(self):
        try:
            self._ssh.python.execute("%s.pop(%i, None)" % (OBJECT_CACHE_NAME, self._id))
        except Exception:
            pass

    def __repr__(self):
        return "RemoteProxy(%r, %i)" % (type(self).__name__, self._id)


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
            func = library_fn(func_name, wraps=getattr(mod, func_name, None))
            setattr(cls, func_name, func)
        cls._PROXY_FUNCS_LOADED = True

    def __init__(self, ssh):
        self._ssh = ssh

    @fin.cache.property
    def _runner(self):
        self._ssh.python.execute("import %s" % self._MODULE_NAME)
        return self._ssh.python
