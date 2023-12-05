from __future__ import print_function
import unittest
import collections

import titantuner


class Test(unittest.TestCase):
    def test_get_filenames(self):
        filenames = titantuner.source.TitanSource.get_filenames(["files/1/"])
        self.assertEqual(filenames, ["files/1/file1", "files/1/file2.txt"])

        filenames = titantuner.source.TitanSource.get_filenames(["files/1/*.txt"])
        self.assertEqual(filenames, ["files/1/file2.txt"])


if __name__ == "__main__":
    unittest.main()
