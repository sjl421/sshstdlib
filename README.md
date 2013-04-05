sshstdlib [![Build Status](https://travis-ci.org/stestagg/sshstdlib.png)](https://travis-ci.org/stestagg/sshstdlib)
=========

sshstdlib emulates the python standard libraries, operating over an SSH tunnel.

It uses paramiko to set up an SSH session, and allows simple remote execution
and familiar methods on the remote system.

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
