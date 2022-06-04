import os
import unittest
from unittest import mock
from secure_squash_root.distributions.arch import ArchLinuxConfig
from secure_squash_root.exec import exec_binary
from tests.unit.test_helper import PROJECT_ROOT, get_test_files_path

TEST_FILES_DIR = get_test_files_path("distributions/arch")


class ArchLinuxConfigTest(unittest.TestCase):

    @mock.patch("secure_squash_root.distributions.arch.read_text_from")
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

    def test__efi_dirname(self):
        arch = ArchLinuxConfig()
        self.assertEqual(arch.efi_dirname(), "Arch")

    def test__vmlinuz(self):
        arch = ArchLinuxConfig()
        self.assertEqual(arch.vmlinuz("5.17.2-arch"),
                         "/usr/lib/modules/5.17.2-arch/vmlinuz")

    def test__build_initramfs_with_microcode(self):
        pass
        # TODO

    @mock.patch("secure_squash_root.distributions.arch.os.listdir")
    def test__list_kernel(self, mock):
        arch = ArchLinuxConfig()
        result = arch.list_kernel()
        mock.assert_called_once_with("/usr/lib/modules")
        self.assertEqual(result, mock())

    @mock.patch("secure_squash_root.distributions.arch.read_text_from")
    @mock.patch("secure_squash_root.distributions.arch.exec_binary")
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
            '/root/git/usr/lib/secure-squash-root/mkinitcpio_list_presets',
            '../../root/git/tests/unit/files/distributions/arch/linux_name'])
