
from __future__ import with_statement

import subprocess

import fin.testing


import sshstdlib.testcommon as testcommon
import sshstdlib.library


class SubprocessTest(testcommon.ServerBasedTest):

    def test_check_output(self):
        if not hasattr(subprocess, "check_output"):
            raise fin.testing.unittest.SkipTest("check_output not present")
        self.assertEqual(self.client.subprocess.check_output(["echo", "hi"]), "hi\n")

    def test_popen(self):
        subprocess = self.client.subprocess
        proc = subprocess.Popen(["echo", "hi"], stdout=subprocess.PIPE)
        assert isinstance(proc, sshstdlib.library.RemoteObject)
        stdout, stderr = proc.communicate()
        self.assertEqual(stdout, "hi\n")
        self.assertEqual(stderr, None)

    def test_reading(self):
        subprocess = self.client.subprocess
        proc = subprocess.Popen(["echo", "hi"], stdout=subprocess.PIPE)
        self.assertEqual(proc.stdout.read(), "hi\n")
    
    def test_file_integration(self):
        subprocess = self.client.subprocess
        with self.client.tempfile.NamedTemporaryFile() as fh:
            fh.write("Test")
            fh.flush()
            proc = subprocess.Popen(["cat", fh.name], stdout=subprocess.PIPE)
            self.assertEqual(proc.stdout.read(), "Test")    

    def test_cwd(self):
        subprocess = self.client.subprocess
        proc = subprocess.Popen(["pwd"], cwd=self.client.tempfile.gettempdir(), 
                                stdout=subprocess.PIPE)
        self.assertEqual(proc.stdout.read().strip(), 
                         self.client.tempfile.gettempdir())

    def test_env(self):
        subprocess = self.client.subprocess
        proc = subprocess.Popen(["env"], env={"a": "b"}, 
                                stdout=subprocess.PIPE)
        self.assertEqual(proc.stdout.read().strip(), "a=b")

if __name__ == "__main__":
    fin.testing.main()