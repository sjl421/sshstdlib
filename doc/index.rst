.. sshstdlib documentation master file, created by
   sphinx-quickstart on Fri Apr  5 12:04:49 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

SSHStdLib API
==============

sshstdlib emulates the python standard libraries, operating over an SSH transport.


Contents:

.. toctree::
   :maxdepth: 3
   
   client


Simple Example
===============

The following snippet shows writing to a temporary file on a 'remote' machine using ipython::

    In [1]: import sshstdlib.client
    
    In [2]: remote = sshstdlib.client.Client.connect("localhost", username="jenkins", password="XXXXXX", no_keys=True)
    
    In [3]: with remote.tempfile.NamedTemporaryFile() as fh:
       ...:     fh.write("hello world")
       ...:     print fh.name
       ...:     
    /tmp/tmpRthB9D
    
    In [4]: remote.os.path.exists("/tmp/tmpRthB9D")
    Out[4]: False

In this example, a file is copied to the remote machine, and then the sha1sum compared::

    import hashlib
    import sys

    import sshstdlib.client


    def main(path):
        client = sshstdlib.client.Client.connect("localhost", username="jenkins", password="XXXXXX", no_keys=True)
        
        with open(path, "rb") as fh:
            local_sha1 = hashlib.sha1(fh.read()).hexdigest()

        Local = client.shutil.Local
        with client.tempfile.NamedTemporaryFile() as dest:
            client.shutil.copy(Local(path), dest.name)
            remote_sha1 = client.check_call("sha1sum", dest.name).split(" ", 1)[0]
        if local_sha1 == remote_sha1:
            print "Files are equal"


    if __name__ == "__main__":
        sys.exit(main("/proc/version"))


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

