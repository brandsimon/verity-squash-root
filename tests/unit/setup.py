import unittest
from unittest import mock
from secure_squash_root.setup import add_uefi_boot_option, add_kernels_to_uefi
from tests.unit.distributions.base import distribution_mock


class SetupTest(unittest.TestCase):

    @mock.patch("secure_squash_root.setup.exec_binary")
    def test__add_uefi_boot_option(self, mock):
        add_uefi_boot_option("/dev/sda", 1, "Arch Linux",
                             "/EFI/Arch/linux.efi")
        mock.assert_called_once_with(
            ["efibootmgr", "--disk", "/dev/sda", "--part", "1",
             "--create", "--label", "Arch Linux", "--loader",
             "/EFI/Arch/linux.efi"])

    @mock.patch("secure_squash_root.setup.add_uefi_boot_option")
    def test__add_kernels_to_uefi(self, boot_mock):
        distri_mock = distribution_mock()
        ignore = " linux-lts_default_tmpfs ,linux_fallback"
        config = {
            "DEFAULT": {
                "IGNORE_KERNEL_EFIS": ignore,
            }
        }
        add_kernels_to_uefi(config, distri_mock, "/dev/vda", 3)
        self.assertEqual(
            boot_mock.mock_calls,
            [mock.call('/dev/vda', 3, 'Distri Linux-lts (default)',
                       '/EFI/Arch/linux-lts_default.efi'),
             mock.call('/dev/vda', 3, 'Distri Linux (fallback) tmpfs',
                       '/EFI/Arch/linux_fallback_tmpfs.efi'),
             mock.call('/dev/vda', 3, 'Distri Linux (default) tmpfs',
                       '/EFI/Arch/linux_default_tmpfs.efi'),
             mock.call('/dev/vda', 3, 'Distri Linux (default)',
                       '/EFI/Arch/linux_default.efi')])
