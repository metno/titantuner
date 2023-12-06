from __future__ import print_function
import unittest
import collections
import os

import titantuner


class Test(unittest.TestCase):
    def test_get_filenames(self):
        dir = os.path.dirname(os.path.realpath(__file__)).rstrip('/') + "/"
        filenames = titantuner.source.TitanSource.get_filenames([f"{dir}files/1/"])
        self.assertEqual(filenames, [f"{dir}files/1/file1", f"{dir}files/1/file2.txt"])

        filenames = titantuner.source.TitanSource.get_filenames([f"{dir}files/1/*.txt"])
        self.assertEqual(filenames, [f"{dir}files/1/file2.txt"])


if __name__ == "__main__":
    unittest.main()
