import unittest
from pathlib import Path
from unittest import mock
from verity_squash_root.distributions.debian import DebianConfig


class DebianConfigTest(unittest.TestCase):

    def test__efi_dirname(self):
        debian = DebianConfig("ubuntu", "Kali")
        self.assertEqual(debian.efi_dirname(), "ubuntu")

    def test__kernel_to_name(self):
        debian = DebianConfig("debian", "Debian GNU/Linux")
        debian.list_kernels = mock.Mock(
            return_value=["6.1.13", "5.15.2", "5.4"])
        self.assertEqual(debian.kernel_to_name("6.1.13"),
                         "current")
        self.assertEqual(debian.kernel_to_name("5.15.2"),
                         "old")
        self.assertEqual(debian.kernel_to_name("5.4"),
                         "old_x2")

    def test__vmlinuz(self):
        debian = DebianConfig("debian", "Debian GNU/Linux")
        self.assertEqual(debian.vmlinuz("5.17.2-debian"),
                         Path("/boot/vmlinuz-5.17.2-debian"))

    def test__display_name(self):
        debian = DebianConfig("debian", "Debian GNU/Linux")
        self.assertEqual(debian.display_name(), "Debian GNU/Linux")

    @mock.patch("verity_squash_root.distributions."
                "base.DistributionConfig._modules_dir")
    def test__list_kernels(self, mock):
        mock.iterdir.return_value = [Path("/usr/lib/modules/5.16.4"),
                                     Path("/usr/lib/modules/5.11.2"),
                                     Path("/usr/lib/modules/5.13.2")]
        debian = DebianConfig("debian", "Debian GNU/Linux")
        result = debian.list_kernels()
        mock.iterdir.assert_called_once_with()
        self.assertEqual(result, ["5.16.4", "5.13.2", "5.11.2"])

    def test__microcode_paths(self):
        debian = DebianConfig("debian", "Debian GNU/Linux")
        with self.assertRaises(NotImplementedError) as e:
            debian.microcode_paths()
            self.assertEqual(str(e), "Base class")
