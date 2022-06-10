import os
import unittest
from .test_helper import get_test_files_path, wrap_tempdir
from secure_squash_root.file_op import read_text_from, write_str_to, \
    merge_files, read_from

TEST_FILES_DIR = get_test_files_path("file_op")
READ_TXT = os.path.join(TEST_FILES_DIR, "read.txt")
READ_TXT_CONTENT = "This is a test str.\n"


class FileOPTest(unittest.TestCase):

    def test__read_from(self):
        result = read_from(READ_TXT)
        self.assertEqual(result, bytes(READ_TXT_CONTENT, "utf-8"))

    def test__read_text_from(self):
        result = read_text_from(READ_TXT)
        self.assertEqual(result, READ_TXT_CONTENT)

    @wrap_tempdir
    def test__write_str_to(self, tempdir):
        path = os.path.join(tempdir, "testfile")
        text = "Some test string\nnext line"
        write_str_to(path, text)
        self.assertEqual(read_text_from(path), text)

    @wrap_tempdir
    def test__merge_files(self, tempdir):
        in1 = os.path.join(tempdir, "in1")
        in3 = os.path.join(tempdir, "in2")
        in1_text = "First part\n"
        in3_text = "Third part\n"
        out = os.path.join(tempdir, "my_out_file")
        write_str_to(in1, in1_text)
        write_str_to(in3, in3_text)
        merge_files([in1, READ_TXT, in3, READ_TXT], out)
        self.assertEqual(read_text_from(out),
                         "{}{}{}{}".format(
                             in1_text, READ_TXT_CONTENT,
                             in3_text, READ_TXT_CONTENT))
