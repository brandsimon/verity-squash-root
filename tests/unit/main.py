import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import call
from tests.unit.distributions.base import distribution_mock
from verify_squash_root.main import move_kernel_to, \
    create_squashfs_return_verity_hash, build_and_move_kernel, \
    create_image_and_sign_kernel


class MainTest(unittest.TestCase):

    def test__move_kernel_to(self):
        base = "verify_squash_root.main"
        all_mocks = mock.Mock()

        with (mock.patch("{}.shutil".format(base),
                         new=all_mocks.shutil),
              mock.patch("{}.efi".format(base),
                         new=all_mocks.efi)):
            # Kernel does not exist yet
            all_mocks.dest.exists.return_value = False
            move_kernel_to(all_mocks.src,
                           all_mocks.dest,
                           "a",
                           all_mocks.backup)
            self.assertEqual(
                all_mocks.mock_calls,
                [call.dest.exists(),
                 call.shutil.move(all_mocks.src,
                                  all_mocks.dest)])

            all_mocks.reset_mock()
            # Kernel exist, backup not supplied
            all_mocks.dest.exists.return_value = True
            move_kernel_to(all_mocks.src,
                           all_mocks.dest,
                           "a",
                           None)
            self.assertEqual(
                list(all_mocks.mock_calls),
                [call.dest.exists(),
                 call.efi.file_matches_slot_or_is_broken(
                     all_mocks.dest, "a"),
                 call.dest.unlink(),
                 call.shutil.move(all_mocks.src,
                                  all_mocks.dest)])

            all_mocks.reset_mock()
            # Kernel exist, slot does not match
            all_mocks.dest.exists.return_value = True
            all_mocks.efi.file_matches_slot_or_is_broken.return_value = False
            move_kernel_to(all_mocks.src,
                           all_mocks.dest,
                           "b",
                           all_mocks.backup)
            self.assertEqual(
                all_mocks.mock_calls,
                [call.dest.exists(),
                 call.efi.file_matches_slot_or_is_broken(all_mocks.dest, "b"),
                 call.dest.replace(all_mocks.backup),
                 call.shutil.move(all_mocks.src,
                                  all_mocks.dest)])

            all_mocks.reset_mock()
            # Kernel exist, slot matches
            all_mocks.dest.exists.return_value = True
            all_mocks.efi.file_matches_slot_or_is_broken.return_value = True
            move_kernel_to(all_mocks.src,
                           all_mocks.dest,
                           "a",
                           all_mocks.backup)
            self.assertEqual(
                all_mocks.mock_calls,
                [call.dest.exists(),
                 call.efi.file_matches_slot_or_is_broken(all_mocks.dest, "a"),
                 call.dest.unlink(),
                 call.shutil.move(all_mocks.src,
                                  all_mocks.dest)])

    def test__create_squashfs_return_verity_hash(self):
        base = "verify_squash_root.main"
        all_mocks = mock.Mock()

        config = {
            "DEFAULT": {
                "ROOT_MOUNT": "/opt/mnt/root",
                "EFI_PARTITION": "/boot/second/efi",
                "EXCLUDE_DIRS": "var/lib,opt/var",
            }
        }

        with (mock.patch("{}.veritysetup_image".format(base),
                         new=all_mocks.veritysetup_image),
              mock.patch("{}.mksquashfs".format(base),
                         new=all_mocks.mksquashfs)):
            result = create_squashfs_return_verity_hash(config, "c")
            self.assertEqual(
                all_mocks.mock_calls,
                [call.mksquashfs(['var/lib', 'opt/var'],
                                 Path('/opt/mnt/root/image_c.squashfs'),
                                 Path('/opt/mnt/root'),
                                 Path('/boot/second/efi')),
                 call.veritysetup_image(
                     Path('/opt/mnt/root/image_c.squashfs'))])
            self.assertEqual(
                result,
                all_mocks.veritysetup_image())

    def test__build_and_move_kernel(self):
        base = "verify_squash_root.main"
        all_mocks = mock.Mock()
        config = mock.Mock()
        vmlinuz = mock.Mock()
        initramfs = mock.Mock()
        use_slot = mock.Mock()
        root_hash = mock.Mock()
        cmdline_add = mock.Mock()

        with (mock.patch("{}.efi".format(base),
                         new=all_mocks.efi),
              mock.patch("{}.move_kernel_to".format(base),
                         new=all_mocks.move_kernel_to)):
            # No install
            build_and_move_kernel(
                config, vmlinuz, initramfs, use_slot, root_hash,
                cmdline_add, "linux_fallback", Path("/boot/ef/EFI/Debian"),
                "Debian Linux", ["linux", "linux_fallback", "linux-lts"])
            self.assertEqual(all_mocks.mock_calls, [])

            # No backup
            build_and_move_kernel(
                config, vmlinuz, initramfs, use_slot, root_hash,
                cmdline_add, "linux_fallback", Path("/boot/ef/EFI/Debian"),
                "Debian Linux", ["linux", "linux_fallback_backup", "lts_lin"])

            self.assertEqual(
                all_mocks.mock_calls,
                [call.efi.build_and_sign_kernel(
                     config, vmlinuz, initramfs, use_slot, root_hash,
                     Path('/tmp/verify_squash_root/tmp.efi'), cmdline_add),
                 call.move_kernel_to(
                     Path('/tmp/verify_squash_root/tmp.efi'),
                     Path('/boot/ef/EFI/Debian/linux_fallback.efi'),
                     use_slot, None)])

            all_mocks.reset_mock()
            # Backup
            build_and_move_kernel(
                config, vmlinuz, initramfs, use_slot, root_hash,
                cmdline_add, "linux_tmpfs", Path("/boot/efidir/EFI/Debian"),
                "Debian Linux 11", ["linux", "linux_tmp", "lts_lin"])
            self.assertEqual(
                all_mocks.mock_calls,
                [call.efi.build_and_sign_kernel(
                     config, vmlinuz, initramfs, use_slot, root_hash,
                     Path('/tmp/verify_squash_root/tmp.efi'), cmdline_add),
                 call.move_kernel_to(
                     Path('/tmp/verify_squash_root/tmp.efi'),
                     Path('/boot/efidir/EFI/Debian/linux_tmpfs.efi'),
                     use_slot,
                     Path('/boot/efidir/EFI/Debian/linux_tmpfs_backup.efi'))])

    def test__create_image_and_sign_kernel(self):
        base = "verify_squash_root.main"
        all_mocks = mock.Mock()
        cmdline = mock.Mock()
        use_slot = mock.Mock()
        root_hash = mock.Mock()

        def initrdfunc(kernel, preset):
            return Path("/path/initramfs_{}_{}.img".format(kernel, preset))

        config = {
            "DEFAULT": {
                "EFI_PARTITION": "/boot/efi",
                "IGNORE_KERNEL_EFIS":
                    " linux_default ,linux_default_tmpfs ,linux_fallback_tmpfs"
                    ",linux_lts_t",
            }
        }
        ignored_efis = ["linux_default", "linux_default_tmpfs",
                        "linux_fallback_tmpfs", "linux_lts_t"]
        with (mock.patch("{}.read_text_from".format(base),
                         new=all_mocks.read_text_from),
              mock.patch("{}.cmdline".format(base),
                         new=all_mocks.cmdline),
              mock.patch("{}.create_squashfs_return_verity_hash".format(base),
                         new=all_mocks.create_squashfs_return_verity_hash),
              mock.patch("{}.build_and_move_kernel".format(base),
                         new=all_mocks.build_and_move_kernel),
              mock.patch("{}.move_kernel_to".format(base),
                         new=all_mocks.move_kernel_to)):
            distri_mock = distribution_mock()
            distri_mock.build_initramfs_with_microcode.side_effect = initrdfunc
            all_mocks.cmdline.unused_slot.return_value = use_slot
            all_mocks.create_squashfs_return_verity_hash.return_value = \
                root_hash
            all_mocks.read_text_from.return_value = cmdline
            create_image_and_sign_kernel(config, distri_mock)
            self.assertEqual(
                all_mocks.mock_calls,
                [call.read_text_from(Path('/proc/cmdline')),
                 call.cmdline.unused_slot(cmdline),
                 call.create_squashfs_return_verity_hash(config, use_slot),
                 call.build_and_move_kernel(
                     config,
                     Path('/lib64/modules/5.19/vmlinuz'),
                     Path('/path/initramfs_5.19_fallback.img'),
                     use_slot,
                     root_hash,
                     '',
                     'linux_fallback',
                     Path('/boot/efi/EFI/Arch'),
                     'Distri Linux (fallback)',
                     ignored_efis),
                 call.build_and_move_kernel(
                     config,
                     Path('/lib64/modules/5.19/vmlinuz'),
                     Path('/path/initramfs_5.19_fallback.img'),
                     use_slot,
                     root_hash,
                     'verify_squash_root_volatile',
                     'linux_fallback_tmpfs',
                     Path('/boot/efi/EFI/Arch'),
                     'Distri Linux (fallback) tmpfs',
                     ignored_efis),
                 call.build_and_move_kernel(
                     config,
                     Path('/lib64/modules/5.14/vmlinuz'),
                     Path('/path/initramfs_5.14_default.img'),
                     use_slot,
                     root_hash,
                     '',
                     'linux-lts_default',
                     Path('/boot/efi/EFI/Arch'),
                     'Distri Linux-lts (default)',
                     ignored_efis),
                 call.build_and_move_kernel(
                     config,
                     Path('/lib64/modules/5.14/vmlinuz'),
                     Path('/path/initramfs_5.14_default.img'),
                     use_slot,
                     root_hash,
                     'verify_squash_root_volatile',
                     'linux-lts_default_tmpfs',
                     Path('/boot/efi/EFI/Arch'),
                     'Distri Linux-lts (default) tmpfs',
                     ignored_efis)])
            self.assertEqual(
                distri_mock.mock_calls,
                [call.efi_dirname(),
                 call.list_kernels(),
                 call.list_kernel_presets('5.19'),
                 call.file_name('5.19', 'default'),
                 call.vmlinuz('5.19'),
                 call.file_name('5.19', 'default'),
                 call.display_name('5.19', 'default'),
                 call.file_name('5.19', 'fallback'),
                 call.vmlinuz('5.19'),
                 call.file_name('5.19', 'fallback'),
                 call.display_name('5.19', 'fallback'),
                 call.build_initramfs_with_microcode('5.19', 'fallback'),
                 call.list_kernel_presets('5.14'),
                 call.file_name('5.14', 'default'),
                 call.vmlinuz('5.14'),
                 call.file_name('5.14', 'default'),
                 call.display_name('5.14', 'default'),
                 call.build_initramfs_with_microcode('5.14', 'default')])
