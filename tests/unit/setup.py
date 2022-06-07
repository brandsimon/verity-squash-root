import unittest
from unittest import mock
from secure_squash_root.setup import add_uefi_boot_option, \
    add_kernels_to_uefi, setup_systemd_boot
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
        ignore = (" linux-lts_default_backup,"
                  "linux-lts_default_tmpfs ,linux_fallback")
        config = {
            "DEFAULT": {
                "IGNORE_KERNEL_EFIS": ignore,
            }
        }
        add_kernels_to_uefi(config, distri_mock, "/dev/vda", 3)
        self.assertEqual(
            boot_mock.mock_calls,
            [mock.call('/dev/vda', 3,
                       'Distri Linux-lts (default) tmpfs Backup',
                       '/EFI/Arch/linux-lts_default_tmpfs_backup.efi'),
             mock.call('/dev/vda', 3, 'Distri Linux-lts (default)',
                       '/EFI/Arch/linux-lts_default.efi'),
             mock.call('/dev/vda', 3, 'Distri Linux (fallback) tmpfs',
                       '/EFI/Arch/linux_fallback_tmpfs.efi'),
             mock.call('/dev/vda', 3, 'Distri Linux (fallback) tmpfs Backup',
                       '/EFI/Arch/linux_fallback_tmpfs_backup.efi'),
             mock.call('/dev/vda', 3, 'Distri Linux (fallback) Backup',
                       '/EFI/Arch/linux_fallback_backup.efi'),
             mock.call('/dev/vda', 3, 'Distri Linux (default) tmpfs',
                       '/EFI/Arch/linux_default_tmpfs.efi'),
             mock.call('/dev/vda', 3, 'Distri Linux (default) tmpfs Backup',
                       '/EFI/Arch/linux_default_tmpfs_backup.efi'),
             mock.call('/dev/vda', 3, 'Distri Linux (default)',
                       '/EFI/Arch/linux_default.efi'),
             mock.call('/dev/vda', 3, 'Distri Linux (default) Backup',
                       '/EFI/Arch/linux_default_backup.efi')])

    @mock.patch("secure_squash_root.setup.exec_binary")
    @mock.patch("secure_squash_root.setup.write_str_to")
    @mock.patch("secure_squash_root.setup.efi.sign")
    def test__setup_systemd_boot(self, sign_mock, write_to_mock, exec_mock):
        distri_mock = distribution_mock()
        ignore = (" linux-lts_default_tmpfs ,linux_fallback, "
                  "linux_default_backup")
        config = {
            "DEFAULT": {
                "IGNORE_KERNEL_EFIS": ignore,
                "SECURE_BOOT_KEYS": "/secure/path",
                "EFI_PARTITION": "/boot/efi_dir",
            }
        }
        setup_systemd_boot(config, distri_mock)
        exec_mock.assert_called_once_with(["bootctl", "install"])
        boot_efi = "/usr/lib/systemd/boot/efi/systemd-bootx64.efi"
        self.assertEqual(
            sign_mock.mock_calls,
            [mock.call("/secure/path", boot_efi,
                       "/boot/efi/EFI/systemd/systemd-bootx64.efi"),
             mock.call("/secure/path", boot_efi,
                       "/boot/efi/EFI/BOOT/BOOTX64.EFI")])
        text = "title Distri {}\nlinux /EFI/Arch/{}\n"
        path = "/boot/efi_dir/loader/entries/{}"
        self.assertEqual(
            write_to_mock.mock_calls,
            [mock.call(path.format("linux_default.conf"),
                       text.format("Linux (default)", "linux_default.efi")),
             mock.call(path.format("linux_default_tmpfs.conf"),
                       text.format("Linux (default) tmpfs",
                                   "linux_default_tmpfs.efi")),
             mock.call(path.format("linux_default_tmpfs_backup.conf"),
                       text.format("Linux (default) tmpfs Backup",
                                   "linux_default_tmpfs_backup.efi")),
             mock.call(path.format("linux_fallback_backup.conf"),
                       text.format("Linux (fallback) Backup",
                                   "linux_fallback_backup.efi")),
             mock.call(path.format("linux_fallback_tmpfs.conf"),
                       text.format("Linux (fallback) tmpfs",
                                   "linux_fallback_tmpfs.efi")),
             mock.call(path.format("linux_fallback_tmpfs_backup.conf"),
                       text.format("Linux (fallback) tmpfs Backup",
                                   "linux_fallback_tmpfs_backup.efi")),
             mock.call(path.format("linux-lts_default.conf"),
                       text.format("Linux-lts (default)",
                                   "linux-lts_default.efi")),
             mock.call(path.format("linux-lts_default_backup.conf"),
                       text.format("Linux-lts (default) Backup",
                                   "linux-lts_default_backup.efi")),
             mock.call(path.format("linux-lts_default_tmpfs_backup.conf"),
                       text.format("Linux-lts (default) tmpfs Backup",
                                   "linux-lts_default_tmpfs_backup.efi"))])
