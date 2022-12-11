import unittest
from pathlib import Path
from unittest import mock
from verity_squash_root.config import KEY_DIR
from verity_squash_root.setup import add_uefi_boot_option, \
    add_kernels_to_uefi, setup_systemd_boot
from tests.unit.distributions.base import distribution_mock
from tests.unit.initramfs import create_initramfs_mock


class SetupTest(unittest.TestCase):

    @mock.patch("verity_squash_root.setup.exec_binary")
    def test__add_uefi_boot_option(self, mock):
        add_uefi_boot_option("/dev/sda", 1, "Arch Linux",
                             Path("/EFI/Arch/linux.efi"))
        mock.assert_called_once_with(
            ["efibootmgr", "--disk", "/dev/sda", "--part", "1",
             "--create", "--label", "Arch Linux", "--loader",
             "/EFI/Arch/linux.efi"])

    @mock.patch("verity_squash_root.setup.add_uefi_boot_option")
    def test__add_kernels_to_uefi(self, boot_mock):
        distri_mock = distribution_mock()
        initramfs_mock = create_initramfs_mock(distri_mock)
        ignore = (" linux-lts_default_backup,"
                  "linux-lts_default_tmpfs ,linux_fallback")
        config = {
            "DEFAULT": {
                "IGNORE_KERNEL_EFIS": ignore,
            }
        }
        add_kernels_to_uefi(config, distri_mock, initramfs_mock, "/dev/vda", 3)
        efi_path = Path('/EFI/verity_squash_root/ArchEfi')
        self.assertEqual(
            boot_mock.mock_calls,
            [mock.call('/dev/vda', 3, 'Display Linux-lts (default)',
                       efi_path / 'linux-lts_default.efi'),
             mock.call('/dev/vda', 3, 'Display Linux (fallback) tmpfs Backup',
                       efi_path / 'linux_fallback_tmpfs_backup.efi'),
             mock.call('/dev/vda', 3, 'Display Linux (fallback) tmpfs',
                       efi_path / 'linux_fallback_tmpfs.efi'),
             mock.call('/dev/vda', 3, 'Display Linux (default) tmpfs Backup',
                       efi_path / 'linux_default_tmpfs_backup.efi'),
             mock.call('/dev/vda', 3, 'Display Linux (default) tmpfs',
                       efi_path / 'linux_default_tmpfs.efi'),
             mock.call('/dev/vda', 3, 'Display Linux (default) Backup',
                       efi_path / 'linux_default_backup.efi'),
             mock.call('/dev/vda', 3, 'Display Linux (default)',
                       efi_path / 'linux_default.efi')])

    @mock.patch("verity_squash_root.setup.exec_binary")
    @mock.patch("verity_squash_root.setup.write_str_to")
    @mock.patch("verity_squash_root.setup.efi.sign")
    def test__setup_systemd_boot(self, sign_mock, write_to_mock, exec_mock):
        distri_mock = distribution_mock()
        initramfs_mock = create_initramfs_mock(distri_mock)
        ignore = (" linux-lts_default_tmpfs ,linux_fallback, "
                  "linux_default_backup")
        config = {
            "DEFAULT": {
                "IGNORE_KERNEL_EFIS": ignore,
                "SECURE_BOOT_KEYS": "/secure/path",
                "EFI_PARTITION": "/boot/efi_dir",
            }
        }
        setup_systemd_boot(config, distri_mock, initramfs_mock)
        exec_mock.assert_called_once_with(["bootctl", "install"])
        boot_efi = Path("/usr/lib/systemd/boot/efi/systemd-bootx64.efi")
        self.assertEqual(
            sign_mock.mock_calls,
            [mock.call(KEY_DIR, Path(boot_efi),
                       Path("/boot/efi_dir/EFI/systemd/systemd-bootx64.efi")),
             mock.call(KEY_DIR, boot_efi,
                       Path("/boot/efi_dir/EFI/BOOT/BOOTX64.EFI"))])
        text = "title Display {}\nlinux /EFI/verity_squash_root/ArchEfi/{}\n"
        path = Path("/boot/efi_dir/loader/entries")
        self.assertEqual(
            write_to_mock.mock_calls,
            [mock.call(path / "linux_default.conf",
                       text.format("Linux (default)", "linux_default.efi")),
             mock.call(path / "linux_default_tmpfs.conf",
                       text.format("Linux (default) tmpfs",
                                   "linux_default_tmpfs.efi")),
             mock.call(path / "linux_default_tmpfs_backup.conf",
                       text.format("Linux (default) tmpfs Backup",
                                   "linux_default_tmpfs_backup.efi")),
             mock.call(path / "linux_fallback_tmpfs.conf",
                       text.format("Linux (fallback) tmpfs",
                                   "linux_fallback_tmpfs.efi")),
             mock.call(path / "linux_fallback_tmpfs_backup.conf",
                       text.format("Linux (fallback) tmpfs Backup",
                                   "linux_fallback_tmpfs_backup.efi")),
             mock.call(path / "linux-lts_default.conf",
                       text.format("Linux-lts (default)",
                                   "linux-lts_default.efi")),
             mock.call(path / "linux-lts_default_backup.conf",
                       text.format("Linux-lts (default) Backup",
                                   "linux-lts_default_backup.efi"))])
