
from __future__ import with_statement

import os
import sys
import json

import paramiko.client
import fin.testing

import sshstdlib.client
import sshstdlib.testcommon as testcommon


class OSTest(testcommon.ServerBasedTest):

    def test_name(self):
        sshos = self.client.os
        self.assertEqual(os.name, sshos.name)

    def test_environ(self):
        sshos = self.client.os
        environ = sshos.environ
        self.assertFalse("sshos_test" in environ)
        with self.assertRaises(TypeError):
            environ["sshos_test"] = True  
        environ["sshos_test"] = "test"
        self.assertTrue("sshos_test" in environ)
        for value in ["value", "someone's \"test\"", "\x1b"]:
            environ["sshos_test"] = value
            self.client.python.execute("import os")
            new_env = self.client.python.evaluate("dict(os.environ)")
            self.assertEqual(new_env["sshos_test"], value)
        del environ["sshos_test"]
        self.assertFalse("sshos_test" in environ)

    def test_proxy_methods(self):
        for method in ["geteuid", "getuid", "getegid", "getgid"]:
            print >>sys.stderr, method
            self.assertEqual(getattr(self.client.os, method)(), 
                             getattr(os, method)())

    def test_getgroups(self):
        self.assertEqual(self.client.os.getgroups(), os.getgroups())

    def test_strerror(self):
        self.assertEqual(self.client.os.strerror(1),
                         os.strerror(1))

    def test_stat(self):
        self.assertEqual(self.client.os.stat("/tmp"), os.stat("/tmp"))


class OSPathTest(testcommon.ServerBasedTest):

    def test_simple_methods(self):
        for path in set(["/", os.path.expanduser("~/"), "/tmp"]):
            for method in [
                    "abspath",
                    "basename",
                    "commonprefix",
                    "dirname",
                    "exists",
                    "lexists",
                    "expanduser",
                    "expandvars",
                    "getatime",
                    "getmtime",
                    "getctime",
                    "getsize",
                    "isabs",
                    "isfile",
                    "isdir",
                    "islink",
                    "ismount",
                    "normcase",
                    "normpath",
                    "realpath",
                    "split",
                    "splitdrive",
                    "splitext",
                    "splitunc",
                    ]:
                if hasattr(os.path, method):
                    print >>sys.stderr, method
                    self.assertEqual(
                        getattr(self.client.os.path, method)(path),
                        getattr(os.path, method)(path))


if __name__ == "__main__":
    fin.testing.main()