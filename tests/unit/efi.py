import os
import unittest
from .test_helper import get_test_files_path
from unittest import mock
from secure_squash_root.efi import file_matches_slot, sign, \
    create_efi_executable

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

    @mock.patch("secure_squash_root.efi.exec_binary")
    def test__sign(self, mock):
        sign("my/key/dir", "my/in/file", "my/out/file")
        mock.assert_called_once_with(
            ["sbsign",
             "--key", "my/key/dir/db.key",
             "--cert", "my/key/dir/db.crt",
             "--output", "my/out/file",
             "my/in/file"])

    @mock.patch("secure_squash_root.efi.exec_binary")
    def test__create_efi_executable(self, mock):
        create_efi_executable(
            "/my/stub.efi", "/tmp/cmdline", "/usr/vmlinuz",
            "/tmp/initramfs.img", "/tmp/file.efi")
        mock.assert_called_once_with([
            'objcopy',
            '--add-section', '.osrel=/etc/os-release',
            '--change-section-vma', '.osrel=0x20000',
            '--add-section', '.cmdline=/tmp/cmdline',
            '--change-section-vma', '.cmdline=0x30000',
            '--add-section', '.linux=/usr/vmlinuz',
            '--change-section-vma', '.linux=0x2000000',
            '--add-section', '.initrd=/tmp/initramfs.img',
            '--change-section-vma', '.initrd=0x3000000',
            '/my/stub.efi', '/tmp/file.efi'])
