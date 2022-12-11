import unittest
from .test_helper import get_test_files_path
from pathlib import Path
from unittest import mock
from verity_squash_root.config import KEY_DIR
from verity_squash_root.file_op import read_from
from verity_squash_root.efi import file_matches_slot_or_is_broken, sign, \
    create_efi_executable, build_and_sign_kernel, get_cmdline

TEST_FILES_DIR = get_test_files_path("efi")


class EfiTest(unittest.TestCase):

    def test__file_matches_slot_or_is_broken(self):

        def wrapper(path: str, slot: str):
            file = TEST_FILES_DIR / path
            content_before = read_from(file)
            result = file_matches_slot_or_is_broken(file, slot)
            self.assertEqual(content_before, read_from(file),
                             "objcopy modified file (breaks secure boot)")
            return result

        self.assertTrue(wrapper("stub_slot_a.efi", "a"))
        self.assertFalse(wrapper("stub_slot_a.efi", "b"))
        self.assertTrue(wrapper("stub_slot_b.efi", "b"))
        self.assertFalse(wrapper("stub_slot_b.efi", "a"))

        self.assertFalse(wrapper("stub_slot_unkown.efi", "a"))
        self.assertFalse(wrapper("stub_slot_unkown.efi", "b"))

        log_trunc = ["WARNING:root:Old efi file was truncated"]
        with self.assertLogs() as logs:
            self.assertTrue(wrapper("stub_broken.efi", "a"))
        self.assertEqual(logs.output, log_trunc)
        with self.assertLogs() as logs:
            self.assertTrue(wrapper("stub_broken.efi", "b"))
        self.assertEqual(logs.output, log_trunc)

        log_empty = ["WARNING:root:Old efi file was empty"]
        with self.assertLogs() as logs:
            self.assertTrue(wrapper("stub_empty.efi", "a"))
        self.assertEqual(logs.output, log_empty)
        with self.assertLogs() as logs:
            self.assertTrue(wrapper("stub_empty.efi", "b"))
        self.assertEqual(logs.output, log_empty)

    @mock.patch("verity_squash_root.efi.exec_binary")
    def test__sign(self, mock):
        sign(Path("my/key/dir"), Path("my/in/file"), Path("my/out/file"))
        mock.assert_called_once_with(
            ["sbsign",
             "--key", "my/key/dir/db.key",
             "--cert", "my/key/dir/db.crt",
             "--output", "my/out/file",
             "my/in/file"])

    @mock.patch("verity_squash_root.efi.exec_binary")
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

    def test__get_cmdline__configfile(self):
        all_mocks = mock.Mock()
        cmdline = "rw encrypt=/dev/sda2 quiet"
        config = {
            "DEFAULT": {
                "CMDLINE": cmdline,
                "EFI_STUB": "/usr/lib/systemd/mystub.efi",
            }
        }
        base = "verity_squash_root.efi"
        with mock.patch("{}.CMDLINE_FILE".format(base),
                        new=all_mocks.efi.CMDLINE_FILE):
            self.assertEqual(get_cmdline(config), cmdline)
            self.assertEqual(all_mocks.mock_calls, [])

    def test__get_cmdline__etc_file(self):
        all_mocks = mock.Mock()
        config = {
            "DEFAULT": {
                "EFI_STUB": "/usr/lib/systemd/mystub.efi",
            }
        }
        base = "verity_squash_root.efi"
        call = mock.call
        with mock.patch("{}.CMDLINE_FILE".format(base),
                        new=all_mocks.efi.CMDLINE_FILE):
            all_mocks.efi.CMDLINE_FILE.exists.return_value = True
            all_mocks.efi.CMDLINE_FILE.read_text.return_value = \
                " ro param=val\nroot=UUID=x\n kpti=on debugfs=off"
            self.assertEqual(
                get_cmdline(config),
                " ro param=val root=UUID=x  kpti=on debugfs=off")
            self.assertEqual(
                all_mocks.mock_calls,
                [call.efi.CMDLINE_FILE.exists(),
                 call.efi.CMDLINE_FILE.read_text()])

    def test__build_and_sign_kernel(self):
        all_mocks = mock.Mock()
        base = "verity_squash_root.efi"
        config = {
            "DEFAULT": {
                "EFI_STUB": "/usr/lib/systemd/mystub.efi",
            }
        }
        call = mock.call

        with (mock.patch("{}.sign".format(base),
                         new=all_mocks.efi.sign),
              mock.patch("{}.get_cmdline".format(base),
                         new=all_mocks.get_cmdline),
              mock.patch("{}.create_efi_executable".format(base),
                         new=all_mocks.efi.create_efi_executable),
              mock.patch("{}.write_str_to".format(base),
                         new=all_mocks.write_str_to)):
            all_mocks.get_cmdline.return_value = "rw encrypt=/dev/sda2 quiet"
            build_and_sign_kernel(config, Path("/boot/vmlinuz"),
                                  Path("/tmp/initramfs.img"), "a",
                                  "567myhash234", Path("/tmp/file.efi"),
                                  "tmpfsparam")
            self.assertEqual(
                all_mocks.mock_calls,
                [call.get_cmdline(config),
                 call.write_str_to(Path("/tmp/verity_squash_root/cmdline"),
                                   ("rw encrypt=/dev/sda2 quiet rw tmpfsparam "
                                    "verity_squash_root_slot=a "
                                    "verity_squash_root_hash=567myhash234")),
                 call.efi.create_efi_executable(
                     Path("/usr/lib/systemd/mystub.efi"),
                     Path("/tmp/verity_squash_root/cmdline"),
                     Path("/boot/vmlinuz"), Path("/tmp/initramfs.img"),
                     Path("/tmp/file.efi")),
                 call.efi.sign(KEY_DIR, Path("/tmp/file.efi"),
                               Path("/tmp/file.efi"))])

            all_mocks.reset_mock()

            all_mocks.get_cmdline.return_value = "encrypt=/dev/sda2 quiet"
            build_and_sign_kernel(config, Path("/usr/lib/vmlinuz-lts"),
                                  Path("/boot/initramfs_fallback.img"), "b",
                                  "853anotherhash723",
                                  Path("/tmporary/dir/f.efi"),
                                  "")
            self.assertEqual(
                all_mocks.mock_calls,
                [call.get_cmdline(config),
                 call.write_str_to(
                     Path("/tmp/verity_squash_root/cmdline"),
                     ("encrypt=/dev/sda2 quiet rw  verity_squash_root_slot=b "
                      "verity_squash_root_hash=853anotherhash723")),
                 call.efi.create_efi_executable(
                         Path("/usr/lib/systemd/mystub.efi"),
                         Path("/tmp/verity_squash_root/cmdline"),
                         Path("/usr/lib/vmlinuz-lts"),
                         Path("/boot/initramfs_fallback.img"),
                         Path("/tmporary/dir/f.efi")),
                 call.efi.sign(KEY_DIR,
                               Path("/tmporary/dir/f.efi"),
                               Path("/tmporary/dir/f.efi"))])
