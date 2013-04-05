sshstdlib [![Build Status](https://travis-ci.org/stestagg/sshstdlib.png)](https://travis-ci.org/stestagg/sshstdlib)
=========

sshstdlib emulates the python standard libraries, operating over an SSH tunnel.

It uses paramiko to set up an SSH session, and allows simple remote execution
and familiar methods on the remote system.

Goals
=====

The ideal of sshstdlib is to provide a sensible, pragmatic subset of the python standard libraries.
Largely, this is done by dynamically pushing and running a small python client to the box. :module:`sshstdlib.remote_client`.
Some functionality uses the SSH sftp functionality, and some involves running commands directly using the ssh 'exec' channels.

If functionality is missing from sshstdlib that is present in the python standard libraries, this is a 'missing feature'
let us know if you need anything specific, or feel free to contribute implementations.

If sshstdlib behaviour differs in a meaningful way from the equivalent standard library functionality, this is a bug.
Please submit it as such.

Sometimes adding extra functionality makes sense.  This should be done in an unobtrusive manner, and be documented explicitly here.

Example usage
=============

```python
In [1]: import sshstdlib.client

In [2]: remote = sshstdlib.client.Client.connect("localhost", username="jenkins", password="XXXXXX", no_keys=True)

In [3]: with remote.tempfile.NamedTemporaryFile() as fh:
   ...:     fh.write("hello world")
   ...:     print fh.name
   ...:     
/tmp/tmpRthB9D

In [4]: remote.os.path.exists("/tmp/tmpRthB9D")
Out[4]: False

```

Documentation
=============

API Documentation can be found here: https://sshstdlib.readthedocs.org/en/latest/index.html

Notes
=====

Channels are set up only when required, so the python client is only pushed and run when the first call that requires is is made.  likewise with the sftp channel.  both the :attr:`python` and :attr:`sftp` channels are persisted once created for the lifetime of the client.

