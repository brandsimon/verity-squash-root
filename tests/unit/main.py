import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import call
from tests.unit.distributions.base import distribution_mock
from tests.unit.initramfs import create_initramfs_mock
from verity_squash_root.config import KEY_DIR
from verity_squash_root.main import move_kernel_to, \
    create_squashfs_return_verity_hash, build_and_move_kernel, \
    create_image_and_sign_kernel, backup_and_sign_efi, \
    backup_and_sign_extra_files, create_directory


class MainTest(unittest.TestCase):

    def test__move_kernel_to(self):
        base = "verity_squash_root.main"
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
        base = "verity_squash_root.main"
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
            result = create_squashfs_return_verity_hash(
                config, Path("/tmp/test.img"))
            self.assertEqual(
                all_mocks.mock_calls,
                [call.mksquashfs(['var/lib', 'opt/var'],
                                 Path('/tmp/test.img'),
                                 Path('/opt/mnt/root'),
                                 Path('/boot/second/efi')),
                 call.veritysetup_image(
                     Path('/tmp/test.img'))])
            self.assertEqual(
                result,
                all_mocks.veritysetup_image())

    def test__create_directory(self):
        path = mock.Mock()
        create_directory(path)
        self.assertEqual(
            path.mock_calls,
            [call.mkdir(parents=True, exist_ok=True)])

    def test__build_and_move_kernel(self):
        base = "verity_squash_root.main"
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
                     Path('/tmp/verity_squash_root/tmp.efi'), cmdline_add),
                 call.move_kernel_to(
                     Path('/tmp/verity_squash_root/tmp.efi'),
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
                     Path('/tmp/verity_squash_root/tmp.efi'), cmdline_add),
                 call.move_kernel_to(
                     Path('/tmp/verity_squash_root/tmp.efi'),
                     Path('/boot/efidir/EFI/Debian/linux_tmpfs.efi'),
                     use_slot,
                     Path('/boot/efidir/EFI/Debian/linux_tmpfs_backup.efi'))])

    def test__create_image_and_sign_kernel(self):
        base = "verity_squash_root.main"
        all_mocks = mock.Mock()
        cmdline = mock.Mock()
        use_slot = mock.Mock()
        root_hash = mock.Mock()

        def initrdfunc(kernel, preset):
            return Path("/path/initramfs_{}_{}.img".format(kernel, preset))

        config = {
            "DEFAULT": {
                "ROOT_MOUNT": "/opt/mnt/root",
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
              mock.patch("{}.create_directory".format(base),
                         new=all_mocks.create_directory),
              mock.patch("{}.create_squashfs_return_verity_hash".format(base),
                         new=all_mocks.create_squashfs_return_verity_hash),
              mock.patch("{}.build_and_move_kernel".format(base),
                         new=all_mocks.build_and_move_kernel),
              mock.patch("{}.shutil".format(base),
                         new=all_mocks.shutil),
              mock.patch("{}.move_kernel_to".format(base),
                         new=all_mocks.move_kernel_to)):
            distri_mock = distribution_mock()
            # create separate mock, since otherwise all_mock history will be
            # full # with initramfs calls to distribution.
            initramfs_mock = create_initramfs_mock(distribution_mock())
            distri_initramfs_mock = mock.Mock()
            distri_initramfs_mock.distri = distri_mock
            distri_initramfs_mock.initramfs = initramfs_mock
            initramfs_mock.build_initramfs_with_microcode.side_effect = \
                initrdfunc
            all_mocks.cmdline.unused_slot.return_value = use_slot
            all_mocks.create_squashfs_return_verity_hash.return_value = \
                root_hash
            all_mocks.read_text_from.return_value = cmdline
            create_image_and_sign_kernel(config, distri_mock, initramfs_mock)
            efi_path = Path('/boot/efi/EFI/verity_squash_root/ArchEfi')
            self.assertEqual(
                all_mocks.mock_calls,
                [call.read_text_from(Path('/proc/cmdline')),
                 call.cmdline.unused_slot(cmdline),
                 call.create_directory(Path(
                     "/boot/efi/EFI/verity_squash_root/ArchEfi")),
                 call.create_squashfs_return_verity_hash(
                     config,
                     Path('/tmp/verity_squash_root/tmp.squashfs')),
                 call.build_and_move_kernel(
                     config,
                     Path('/lib64/modules/5.19/vmlinuz'),
                     Path('/path/initramfs_5.19_fallback.img'),
                     use_slot,
                     root_hash,
                     '',
                     'linux_fallback',
                     efi_path,
                     'Display Linux (fallback)',
                     ignored_efis),
                 call.build_and_move_kernel(
                     config,
                     Path('/lib64/modules/5.19/vmlinuz'),
                     Path('/path/initramfs_5.19_fallback.img'),
                     use_slot,
                     root_hash,
                     'verity_squash_root_volatile',
                     'linux_fallback_tmpfs',
                     efi_path,
                     'Display Linux (fallback) tmpfs',
                     ignored_efis),
                 call.build_and_move_kernel(
                     config,
                     Path('/lib64/modules/5.14/vmlinuz'),
                     Path('/path/initramfs_5.14_default.img'),
                     use_slot,
                     root_hash,
                     '',
                     'linux-lts_default',
                     efi_path,
                     'Display Linux-lts (default)',
                     ignored_efis),
                 call.build_and_move_kernel(
                     config,
                     Path('/lib64/modules/5.14/vmlinuz'),
                     Path('/path/initramfs_5.14_default.img'),
                     use_slot,
                     root_hash,
                     'verity_squash_root_volatile',
                     'linux-lts_default_tmpfs',
                     efi_path,
                     'Display Linux-lts (default) tmpfs',
                     ignored_efis),
                 call.shutil.move(
                     Path('/tmp/verity_squash_root/tmp.squashfs'),
                     Path('/opt/mnt/root/image_{}.squashfs'.format(use_slot))),
                 call.shutil.move(
                     Path('/tmp/verity_squash_root/tmp.squashfs.verity'),
                     Path('/opt/mnt/root/image_{}.squashfs.verity'.format(
                         use_slot)))])
            self.assertEqual(
                distri_initramfs_mock.mock_calls,
                [call.distri.efi_dirname(),
                 call.distri.list_kernels(),
                 call.initramfs.list_kernel_presets('5.19'),
                 call.initramfs.file_name('5.19', 'default'),
                 call.distri.vmlinuz('5.19'),
                 call.initramfs.file_name('5.19', 'default'),
                 call.initramfs.display_name('5.19', 'default'),
                 call.initramfs.file_name('5.19', 'fallback'),
                 call.distri.vmlinuz('5.19'),
                 call.initramfs.file_name('5.19', 'fallback'),
                 call.initramfs.display_name('5.19', 'fallback'),
                 call.initramfs.build_initramfs_with_microcode(
                     '5.19', 'fallback'),
                 call.initramfs.list_kernel_presets('5.14'),
                 call.initramfs.file_name('5.14', 'default'),
                 call.distri.vmlinuz('5.14'),
                 call.initramfs.file_name('5.14', 'default'),
                 call.initramfs.display_name('5.14', 'default'),
                 call.initramfs.build_initramfs_with_microcode(
                     '5.14', 'default')])

    def test__backup_and_sign_efi(self):
        base = "verity_squash_root.main"
        all_mocks = mock.Mock()
        with mock.patch("{}.efi".format(base),
                        new=all_mocks.efi):
            dest = all_mocks.dest
            dest.exists.return_value = False
            backup_and_sign_efi(all_mocks.source, dest)
            self.assertEqual(
                all_mocks.mock_calls,
                [call.dest.exists(),
                 call.efi.sign(KEY_DIR, all_mocks.source, dest)])

    def test__backup_and_sign_efi__backup(self):
        base = "verity_squash_root.main"
        all_mocks = mock.Mock()
        with mock.patch("{}.efi".format(base),
                        new=all_mocks.efi):
            dest = all_mocks.dest
            dest.exists.return_value = True
            dest.parent = Path("/parent/dir")
            dest.stem = "myfile"
            dest.suffix = ".efi"
            replace = Path("/parent/dir/myfile_backup.efi")
            backup_and_sign_efi(all_mocks.source, dest)
            self.assertEqual(
                all_mocks.mock_calls,
                [call.dest.exists(),
                 call.dest.replace(replace),
                 call.efi.sign(KEY_DIR, all_mocks.source, dest)])

    def test__backup_and_sign_extra_files(self):
        base = "verity_squash_root.main"
        all_mocks = mock.Mock()
        config = {
            "EXTRA_SIGN": {
                "systemd": "/usr/lib/systemd/boot/efi/systemd-bootx64.efi => "
                           " /boot/efi/EFI/systemd/systemd-bootx64.efi",
                "fwupd": "/usr/lib/fwupd/fwupd.efi => /boot/fwupd.efi ",
            }
        }
        with mock.patch("{}.backup_and_sign_efi".format(base),
                        new=all_mocks.backup_and_sign_efi):
            backup_and_sign_extra_files(config)
            self.assertEqual(
                all_mocks.mock_calls,
                [call.backup_and_sign_efi(
                     Path("/usr/lib/systemd/boot/efi/systemd-bootx64.efi"),
                     Path("/boot/efi/EFI/systemd/systemd-bootx64.efi")),
                 call.backup_and_sign_efi(
                     Path("/usr/lib/fwupd/fwupd.efi"),
                     Path("/boot/fwupd.efi"))])

    def test__backup_and_sign_extra_files__exception(self):
        base = "verity_squash_root.main"
        all_mocks = mock.Mock()
        config = {
            "EXTRA_SIGN": {
                "systemd": "/usr/lib/systemd/boot/efi/systemd-bootx64.efi => "
                           " /boot/efi/EFI/systemd/systemd-bootx64.efi",
                "fwupd": "/usr/lib/fwupd/fwupd.efi",
                "test": "/x.efi => /y.efi",
            }
        }
        with mock.patch("{}.backup_and_sign_efi".format(base),
                        new=all_mocks.backup_and_sign_efi):
            with self.assertRaises(ValueError) as e:
                backup_and_sign_extra_files(config)
            self.assertEqual(
                str(e.exception),
                "extra signing files need to be specified as\n"
                "name = SOURCE => DEST")
            self.assertEqual(
                all_mocks.mock_calls,
                [call.backup_and_sign_efi(
                     Path("/usr/lib/systemd/boot/efi/systemd-bootx64.efi"),
                     Path("/boot/efi/EFI/systemd/systemd-bootx64.efi"))])
