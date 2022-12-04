import unittest
from unittest.mock import Mock, call, patch
from verity_squash_root.config import TMPDIR
from verity_squash_root.initramfs.dracut import Dracut


class DracutTest(unittest.TestCase):

    def test__file_name(self):
        distri = Mock()
        dracut = Dracut(distri)
        res = dracut.file_name("5.17.2", "not used")
        self.assertEqual(distri.mock_calls, [call.kernel_to_name("5.17.2")])
        self.assertEqual(res, distri.kernel_to_name())

    def test__display_name(self):
        distri = Mock()
        distri.display_name.return_value = "Debian"
        distri.kernel_to_name.return_value = "hardened-linux"
        dracut = Dracut(distri)
        res = dracut.display_name("5.17.2", "random")
        self.assertEqual(
            distri.mock_calls,
            [call.kernel_to_name("5.17.2"),
             call.display_name()])
        self.assertEqual(res, "Debian Hardened linux")

    @patch("verity_squash_root.initramfs.dracut.exec_binary")
    def test__build_initramfs_with_microcode(self, exec_mock):
        distri = Mock()
        dracut = Dracut(distri)
        result = dracut.build_initramfs_with_microcode("5.17.2", "rr")
        self.assertEqual(result, TMPDIR / "5.17.2-rr.image")
        self.assertEqual(distri.mock_calls, [])
        self.assertEqual(
            exec_mock.mock_calls,
            [call(["dracut",
                   "--kver", "5.17.2",
                   "--no-uefi",
                   "--early-microcode",
                   "--add",
                   "verity-squash-root",
                   str(TMPDIR / "5.17.2-rr.image")])])

    def test__list_kernel_presets(self):
        distri = Mock()
        dracut = Dracut(distri)
        self.assertEqual(dracut.list_kernel_presets("5.17.2"), [""])
