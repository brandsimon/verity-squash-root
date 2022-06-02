import os
import unittest
from .test_helper import get_test_files_path, wrap_tempdir
from secure_squash_root.file_op import read_text_from, write_str_to

TEST_FILES_DIR = get_test_files_path("file_op")


class FileOPTest(unittest.TestCase):

    def test__read_text_from(self):
        result = read_text_from(os.path.join(TEST_FILES_DIR, "read.txt"))
        self.assertEqual(result, "This is a test str.\n")

    @wrap_tempdir
    def test__write_str_to(self, tempdir):
        path = os.path.join(tempdir, "testfile")
        text = "Some test string\nnext line"
        write_str_to(path, text)
        self.assertEqual(read_text_from(path), text)
