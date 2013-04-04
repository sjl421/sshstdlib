
from __future__ import with_statement

import os
import tempfile

import fin

import sshstdlib.sshtempfile
import sshstdlib.testcommon as testcommon


class TempfileTest(testcommon.ServerBasedTest):

    def test_named_temporary_file(self):
        tempfile = self.client.tempfile.NamedTemporaryFile()
        self.assertTrue(os.path.isfile(tempfile.name))
        self.assertTrue(self.client.os.path.isfile(tempfile.name))
        tempfile.close()
        self.assertFalse(os.path.exists(tempfile.name))
        self.assertFalse(self.client.os.path.exists(tempfile.name))
        with self.client.tempfile.NamedTemporaryFile() as fh:
            fh.write("hi")
            fh.flush()
            with open(fh.name, "rb") as local_file:
                self.assertEqual(local_file.read(), "hi")

    def test_mkstemp(self):
        _, tempfile = self.client.tempfile.mkstemp()
        try:
            self.assertTrue(os.path.exists(tempfile))
        finally:
            os.unlink(tempfile)

    def test_mkdtemp(self):
        path = self.client.tempfile.mkdtemp()
        try:
            self.assertTrue(os.path.isdir(path))
        finally:
            os.rmdir(path)

    def test_gettmpdir(self):
        self.assertEqual(self.client.tempfile.gettempdir(), tempfile.gettempdir())


if __name__ == "__main__":
    fin.testing.main()