
from __future__ import with_statement

import os
import shutil
import tempfile
import json

import fin.testing

import sshstdlib.client
import sshstdlib.testcommon as testcommon


class ShutilTest(testcommon.ServerBasedTest):

    def test_copy_tree(self):
        ssh = self.client
        tempdir = tempfile.mkdtemp()
        try:
            os.mkdir(os.path.join(tempdir, "foo"))
            with open(os.path.join(tempdir, "foo", "bar.txt"), "wb") as fh:
                fh.write("baz")
            remote_tempdir = self.client.tempfile.mkdtemp()
            try:
                ssh.shutil.copytree(
                    ssh.shutil.Local(tempdir), 
                    os.path.join(remote_tempdir, "out"))
                with open(os.path.join(
                          remote_tempdir, "out", "foo", "bar.txt"), "rb") as fh:
                    self.assertEqual(fh.read(), "baz")
            finally:
                shutil.rmtree(remote_tempdir)

        finally:
            shutil.rmtree(tempdir)

    def test_copy_remote(self):
        tempdir = tempfile.mkdtemp()
        try:
            from_file = os.path.join(tempdir, "from")
            to_file = os.path.join(tempdir, "to")
            with open(from_file, "wb") as fh:
                fh.write("Foo")
            self.client.shutil.copy(from_file, to_file)
            with open(to_file, "rb") as fh:
                self.assertEqual(fh.read(), "Foo")
        finally:
            shutil.rmtree(tempdir)

    def test_copy_local_remote(self):
        tempdir = tempfile.mkdtemp()
        try:
            from_file = os.path.join(tempdir, "from")
            to_file = os.path.join(tempdir, "to")
            with open(from_file, "wb") as fh:
                fh.write("Foo")
            self.client.shutil.copy(self.client.shutil.Local(from_file), 
                                    to_file)
            with open(to_file, "rb") as fh:
                self.assertEqual(fh.read(), "Foo")
        finally:
            shutil.rmtree(tempdir)

if __name__ == "__main__":
    fin.testing.main()