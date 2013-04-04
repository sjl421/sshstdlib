
from __future__ import with_statement

import fin.testing

import sshstdlib.client
import sshstdlib.testcommon as testcommon


class ShutilTest(testcommon.ServerBasedTest):
    
    def test_python(self):
        self.assertEqual(self.client.python.evaluate("1+1"), 2)
        self.assertEqual(self.client.python.evaluate("range(10)"), range(10))

if __name__ == "__main__":
    fin.testing.main()