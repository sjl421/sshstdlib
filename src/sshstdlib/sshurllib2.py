import urllib
import urllib2
import mimetools  # NOQA

import sshstdlib.library as library


class Request(library.RemoteObject):
    pass

Request._LOAD_PROXY(urllib2.Request)


class Response(library.RemoteObject):
    
    code = library.remote_property("code")
    headers = library.remote_property("headers")
    msg = library.remote_property("msg")

    fileno = library.remote_ob_fn("fileno")
    next = library.remote_ob_fn("next")
    read = library.remote_ob_fn("read", wraps=file.read)
    readline = library.remote_ob_fn("readline", wraps=file.readline)
    readlines = library.remote_ob_fn("readlines", wraps=file.readlines)

    def read_into(self, dest, size=None):
        """Like Response.read, but stores the result in the remote variable ``dest``"""
        library.check_valid_name(dest)
        self._ssh.python.execute("%s=%r.read(%r)" % (dest, self, size))


Response._LOAD_PROXY(urllib.addinfourl)


class Urllib2(library.Library):

    _MODULE_NAME = "urllib2"
    _PROXY_FUNCS = []

    Request = library.cached_object("Request", Request)
    urlopen = library.cached_object("urlopen", Response, wraps=urllib2.urlopen)

       
Urllib2.LOAD_FUNCS()
