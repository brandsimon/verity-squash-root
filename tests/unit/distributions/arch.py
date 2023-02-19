import unittest
from pathlib import Path
from unittest import mock
from verity_squash_root.distributions.arch import ArchLinuxConfig
from tests.unit.test_helper import get_test_files_path

TEST_FILES_DIR = get_test_files_path("distributions/arch")


class ArchLinuxConfigTest(unittest.TestCase):

    def test__efi_dirname(self):
        arch = ArchLinuxConfig()
        self.assertEqual(arch.efi_dirname(), "arch")

    @mock.patch("verity_squash_root.distributions.arch.read_text_from")
    def test__kernel_to_name(self, mock):
        arch = ArchLinuxConfig()
        mock.return_value = " kernel Nom "
        result = arch.kernel_to_name("5.12.2")
        mock.assert_called_once_with(
            Path("/usr/lib/modules") / "5.12.2" / "pkgbase")
        self.assertEqual(result, "kernel Nom")

    def test__vmlinuz(self):
        arch = ArchLinuxConfig()
        self.assertEqual(arch.vmlinuz("5.17.2-arch"),
                         Path("/usr/lib/modules/5.17.2-arch/vmlinuz"))

    def test__display_name(self):
        arch = ArchLinuxConfig()
        self.assertEqual(arch.display_name(), "Arch")

    @mock.patch("verity_squash_root.distributions."
                "base.DistributionConfig._modules_dir")
    def test__list_kernels(self, mock):
        mock.iterdir.return_value = [Path("/usr/lib/modules/5.16.4"),
                                     Path("/usr/lib/modules/5.11.2")]
        arch = ArchLinuxConfig()
        result = arch.list_kernels()
        mock.iterdir.assert_called_once_with()
        self.assertEqual(result, ["5.16.4", "5.11.2"])

    def test__microcode_paths(self):
        arch = ArchLinuxConfig()
        self.assertEqual(arch.microcode_paths(),
                         [Path("/boot/amd-ucode.img"),
                          Path("/boot/intel-ucode.img")])
