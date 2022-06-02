import os
import unittest
from .test_helper import get_test_files_path
from secure_squash_root.efi import file_matches_slot

TEST_FILES_DIR = get_test_files_path("efi")


class EfiTest(unittest.TestCase):

    def test__file_matches_slot(self):

        def wrapper(path: str, slot: str):
            file = os.path.join(TEST_FILES_DIR, path)
            return file_matches_slot(file, slot)

        self.assertTrue(wrapper("stub_slot_a.efi", "a"))
        self.assertFalse(wrapper("stub_slot_a.efi", "b"))
        self.assertTrue(wrapper("stub_slot_b.efi", "b"))
        self.assertFalse(wrapper("stub_slot_b.efi", "a"))

        self.assertFalse(wrapper("stub_slot_unkown.efi", "a"))
        self.assertFalse(wrapper("stub_slot_unkown.efi", "b"))
