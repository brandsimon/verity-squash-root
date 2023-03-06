import unittest
from pathlib import Path
from unittest import mock
from verity_squash_root.distributions.arch import ArchLinuxConfig


class ArchLinuxConfigTest(unittest.TestCase):

    def test__efi_dirname(self):
        arch = ArchLinuxConfig("arch", "Arch")
        self.assertEqual(arch.efi_dirname(), "arch")

    @mock.patch("verity_squash_root.distributions.arch.read_text_from")
    def test__kernel_to_name(self, mock):
        arch = ArchLinuxConfig("arch", "Arch")
        mock.return_value = " kernel Nom "
        result = arch.kernel_to_name("5.12.2")
        mock.assert_called_once_with(
            Path("/usr/lib/modules") / "5.12.2" / "pkgbase")
        self.assertEqual(result, "kernel Nom")

    def test__vmlinuz(self):
        arch = ArchLinuxConfig("arch", "Arch")
        self.assertEqual(arch.vmlinuz("5.17.2-arch"),
                         Path("/usr/lib/modules/5.17.2-arch/vmlinuz"))

    def test__display_name(self):
        arch = ArchLinuxConfig("arch", "Arch")
        self.assertEqual(arch.display_name(), "Arch")

    @mock.patch("verity_squash_root.distributions."
                "base.DistributionConfig._modules_dir")
    def test__list_kernels(self, mock):
        mock.iterdir.return_value = [Path("/usr/lib/modules/5.16.4"),
                                     Path("/usr/lib/modules/5.5.2")]
        arch = ArchLinuxConfig("arch", "Arch")
        result = arch.list_kernels()
        mock.iterdir.assert_called_once_with()
        self.assertEqual(result, ["5.16.4", "5.5.2"])

    def test__microcode_paths(self):
        arch = ArchLinuxConfig("arch", "Arch")
        self.assertEqual(arch.microcode_paths(),
                         [Path("/boot/amd-ucode.img"),
                          Path("/boot/intel-ucode.img")])
