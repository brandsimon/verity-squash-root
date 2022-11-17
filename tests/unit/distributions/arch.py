import unittest
from pathlib import Path
from unittest import mock
from verify_squash_root.distributions.arch import ArchLinuxConfig, \
    Mkinitcpio
from verify_squash_root.exec import exec_binary
from verify_squash_root.config import TMPDIR
from tests.unit.test_helper import PROJECT_ROOT, get_test_files_path

TEST_FILES_DIR = get_test_files_path("distributions/arch")


class ArchLinuxConfigTest(unittest.TestCase):

    def test__efi_dirname(self):
        arch = ArchLinuxConfig()
        self.assertEqual(arch.efi_dirname(), "Arch")

    @mock.patch("verify_squash_root.distributions.arch.read_text_from")
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

    @mock.patch("verify_squash_root.distributions.arch.os.listdir")
    def test__list_kernels(self, mock):
        arch = ArchLinuxConfig()
        result = arch.list_kernels()
        mock.assert_called_once_with(Path("/usr/lib/modules"))
        self.assertEqual(result, mock())

    def test__microcode_paths(self):
        arch = ArchLinuxConfig()
        self.assertEqual(arch.microcode_paths(),
                         [Path("/boot/amd-ucode.img"),
                          Path("/boot/intel-ucode.img")])


class MkinitcpioTest(unittest.TestCase):

    def test__file_name(self):
        def test_file_name(kernel, preset, mock_ret, expected_result):
            arch = mock.Mock()
            arch.kernel_to_name.return_value = mock_ret
            initramfs = Mkinitcpio(arch)
            result = initramfs.file_name(kernel, preset)
            arch.kernel_to_name.assert_called_once_with(kernel)
            self.assertEqual(result, expected_result)

        test_file_name("5.2.43", "default", "linux", "linux")
        test_file_name("5.2.44", "fallback", "linux", "linux_fallback")
        test_file_name("5.19.4", "test", "linux-lts", "linux-lts_test")

    def test__display_name(self):
        def test_display_name(kernel, preset, mock_ret, expected_result):
            arch = mock.Mock()
            initramfs = Mkinitcpio(arch)
            arch.kernel_to_name.return_value = mock_ret
            arch.display_name.return_value = "Arch"
            result = initramfs.display_name(kernel, preset)
            arch.kernel_to_name.assert_called_once_with(kernel)
            self.assertEqual(result, expected_result)

        test_display_name("5.2.43", "default", "linux",
                          "Arch Linux")
        test_display_name("5.2.44", "fallback", "linux",
                          "Arch Linux (fallback)")
        test_display_name("5.19.4", "test", "linux-lts",
                          "Arch Linux lts (test)")

    def test__build_initramfs_with_microcode(self):
        preset_info = "some info\npreset_image = /test\nsome more info\nx=y\n"

        def read(file):
            if file == Path("/etc/mkinitcpio.d/linux-pkg.preset"):
                return preset_info
            raise ValueError(file)

        base = "verify_squash_root.distributions.arch"
        all_mocks = mock.Mock()
        with (mock.patch("{}.merge_initramfs_images".format(base),
                         new=all_mocks.merge_initramfs_images),
              mock.patch("{}.exec_binary".format(base),
                         new=all_mocks.exec_binary),
              mock.patch("{}.read_text_from".format(base),
                         new=all_mocks.read_text_from),
              mock.patch("{}.write_str_to".format(base),
                         new=all_mocks.write_str_to)):
            all_mocks.read_text_from.side_effect = read
            all_mocks.distri.kernel_to_name.return_value = "linux-pkg"
            all_mocks.distri.microcode_paths.return_value = [
                Path("/boot/intel-ucode2.img"),
                Path("/boot/w/amd-ucode.img")]
            initramfs = Mkinitcpio(all_mocks.distri)
            res = initramfs.build_initramfs_with_microcode(
                "5.14.3-arch", "x_preset")
            base_name = "linux-pkg-x_preset"
            call = mock.call
            self.assertEqual(
                all_mocks.mock_calls,
                [call.distri.kernel_to_name("5.14.3-arch"),
                 call.read_text_from(
                     Path("/etc/mkinitcpio.d/linux-pkg.preset")),
                 call.write_str_to(
                     TMPDIR / "linux-pkg-x_preset.preset",
                     ("{}\nPRESETS=('x_preset')\n"
                      "x_preset_image={}/{}.initcpio\n".format(
                          preset_info, TMPDIR, base_name))),
                 call.exec_binary(["mkinitcpio", "-p",
                                   "{}/{}.preset".format(TMPDIR, base_name)]),
                 call.distri.microcode_paths(),
                 call.merge_initramfs_images(TMPDIR / "{}.initcpio".format(
                                                 base_name),
                                             [Path("/boot/intel-ucode2.img"),
                                              Path("/boot/w/amd-ucode.img")],
                                             TMPDIR / "{}.image".format(
                                                 base_name))])
            self.assertEqual(res, TMPDIR / "{}.image".format(base_name))

    @mock.patch("verify_squash_root.distributions.arch.exec_binary")
    def test__list_kernel_presets(self, exec_mock):
        def change_lib_path(cmd):
            self.assertEqual(cmd[1], "linux_name")
            cmd[0] = str(PROJECT_ROOT / cmd[0].strip('/'))
            cmd[1] = "../..{}".format(
                TEST_FILES_DIR / "linux_name")
            return exec_binary(cmd)

        exec_mock.side_effect = change_lib_path
        arch = mock.Mock()
        arch.kernel_to_name.return_value = "linux_name"
        initramfs = Mkinitcpio(arch)
        result = initramfs.list_kernel_presets("5.19.4")
        self.assertEqual(result, ["default", "fallback", "test"])
        arch.kernel_to_name.assert_called_once_with("5.19.4")
        exec_mock.assert_called_once_with([
            str(PROJECT_ROOT /
                'usr/lib/verify-squash-root/mkinitcpio_list_presets'),
            "../..{}".format(
                PROJECT_ROOT /
                'tests/unit/files/distributions/arch/linux_name')])
