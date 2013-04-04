
from __future__ import with_statement

import os
import tempfile

import fin

import sshstdlib.client
import sshstdlib.testcommon as testcommon


class FileOperationsTest(testcommon.ServerBasedTest):

    def test_open(self):
        with tempfile.NamedTemporaryFile() as temp:
            temp.write("Foo")
            temp.flush()
            with self.client.open(temp.name) as fh:
                self.assertEqual(fh.read(), "Foo")

    def test_open_two_files(self):
        with tempfile.NamedTemporaryFile() as temp:
            with tempfile.NamedTemporaryFile() as temp2:
                temp.write("Foo")
                temp.flush()
                temp2.write("Bar")
                temp2.flush()
                with self.client.open(temp.name) as fh:
                    with self.client.open(temp2.name) as fh2:
                        self.assertEqual(fh2.read(), "Bar")
                        self.assertEqual(fh.read(), "Foo")



if __name__ == "__main__":
    fin.testing.main()