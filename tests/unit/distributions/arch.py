import os
import unittest
from unittest import mock
from verify_squash_root.distributions.arch import ArchLinuxConfig
from verify_squash_root.exec import exec_binary
from verify_squash_root.config import TMPDIR
from tests.unit.test_helper import PROJECT_ROOT, get_test_files_path

TEST_FILES_DIR = get_test_files_path("distributions/arch")


class ArchLinuxConfigTest(unittest.TestCase):

    @mock.patch("verify_squash_root.distributions.arch.read_text_from")
    def test__file_name(self, mock):
        def test_file_name(kernel, preset, mock_ret, expected_result):
            mock.reset_mock()
            arch = ArchLinuxConfig()
            mock.return_value = mock_ret
            result = arch.file_name(kernel, preset)
            mock.assert_called_once_with(
                os.path.join("/usr/lib/modules", kernel, "pkgbase"))
            self.assertEqual(result, expected_result)

        test_file_name("5.2.43", "default", "linux", "linux")
        test_file_name("5.2.44", "fallback", "linux", "linux_fallback")
        test_file_name("5.19.4", "test", "linux-lts", "linux-lts_test")

    @mock.patch("verify_squash_root.distributions.arch.read_text_from")
    def test__display_name(self, mock):
        def test_display_name(kernel, preset, mock_ret, expected_result):
            mock.reset_mock()
            arch = ArchLinuxConfig()
            mock.return_value = mock_ret
            result = arch.display_name(kernel, preset)
            mock.assert_called_once_with(
                os.path.join("/usr/lib/modules", kernel, "pkgbase"))
            self.assertEqual(result, expected_result)

        test_display_name("5.2.43", "default", "linux",
                          "Arch Linux")
        test_display_name("5.2.44", "fallback", "linux",
                          "Arch Linux (fallback)")
        test_display_name("5.19.4", "test", "linux-lts",
                          "Arch Linux lts (test)")

    def test__efi_dirname(self):
        arch = ArchLinuxConfig()
        self.assertEqual(arch.efi_dirname(), "Arch")

    def test__vmlinuz(self):
        arch = ArchLinuxConfig()
        self.assertEqual(arch.vmlinuz("5.17.2-arch"),
                         "/usr/lib/modules/5.17.2-arch/vmlinuz")

    def test__build_initramfs_with_microcode(self):
        preset_info = "some info\npreset_image = /test\nsome more info\nx=y\n"

        def read(file):
            if file == "/usr/lib/modules/5.14.3-arch/pkgbase":
                return "linux-pkg"
            if file == "/etc/mkinitcpio.d/linux-pkg.preset":
                return preset_info
            raise ValueError(file)

        base = "verify_squash_root.distributions.arch"
        all_mocks = mock.Mock()
        all_mocks.read_text_from.side_effect = read
        with mock.patch("{}.merge_initramfs_images".format(base),
                        new=all_mocks.merge_initramfs_images), \
             mock.patch("{}.exec_binary".format(base),
                        new=all_mocks.exec_binary), \
             mock.patch("{}.read_text_from".format(base),
                        new=all_mocks.read_text_from), \
             mock.patch("{}.write_str_to".format(base),
                        new=all_mocks.write_str_to):
            arch = ArchLinuxConfig()
            res = arch.build_initramfs_with_microcode(
                "5.14.3-arch", "x_preset")
            base_name = "linux-pkg-x_preset"
            call = mock.call
            self.assertEqual(
                all_mocks.mock_calls,
                [call.read_text_from("/usr/lib/modules/5.14.3-arch/pkgbase"),
                 call.read_text_from("/etc/mkinitcpio.d/linux-pkg.preset"),
                 call.write_str_to(
                     "{}/linux-pkg-x_preset.preset".format(TMPDIR),
                     ("{}\nPRESETS=('x_preset')\n"
                      "x_preset_image={}/{}.initcpio\n".format(
                          preset_info, TMPDIR, base_name))),
                 call.exec_binary(["mkinitcpio", "-p",
                                   "{}/{}.preset".format(TMPDIR, base_name)]),
                 call.merge_initramfs_images("{}/{}.initcpio".format(
                                             TMPDIR, base_name),
                                             ["/boot/intel-ucode.img",
                                              "/boot/amd-ucode.img"],
                                             "{}/{}.image".format(
                                                 TMPDIR, base_name))])
            self.assertEqual(
                res, "{}/{}.image".format(TMPDIR, base_name))

    @mock.patch("verify_squash_root.distributions.arch.os.listdir")
    def test__list_kernels(self, mock):
        arch = ArchLinuxConfig()
        result = arch.list_kernels()
        mock.assert_called_once_with("/usr/lib/modules")
        self.assertEqual(result, mock())

    @mock.patch("verify_squash_root.distributions.arch.read_text_from")
    @mock.patch("verify_squash_root.distributions.arch.exec_binary")
    def test__list_kernel_presets(self, exec_mock, read_mock):
        def change_lib_path(cmd):
            cmd[0] = os.path.join(PROJECT_ROOT, cmd[0].strip('/'))
            cmd[1] = "../..{}".format(
                os.path.join(TEST_FILES_DIR, "linux_name"))
            return exec_binary(cmd)

        read_mock.return_value = b"linux_kernel"
        exec_mock.side_effect = change_lib_path
        arch = ArchLinuxConfig()
        result = arch.list_kernel_presets("5.19.4")
        self.assertEqual(result, ["default", "fallback", "test"])
        read_mock.assert_called_once_with("/usr/lib/modules/5.19.4/pkgbase")
        exec_mock.assert_called_once_with([
            '/root/git/usr/lib/verify-squash-root/mkinitcpio_list_presets',
            '../../root/git/tests/unit/files/distributions/arch/linux_name'])
