import unittest
from pathlib import Path
from unittest import mock
from verity_squash_root.initramfs.mkinitcpio import Mkinitcpio
from verity_squash_root.exec import exec_binary
from verity_squash_root.config import TMPDIR
from tests.unit.test_helper import PROJECT_ROOT, get_test_files_path
from tests.unit.distributions.base import distribution_mock

TEST_FILES_DIR = get_test_files_path("distributions/arch")


class MkinitcpioTest(unittest.TestCase):

    def test__file_name(self):
        mkinitcpio = Mkinitcpio(distribution_mock())
        self.assertEqual(mkinitcpio.file_name("5.19", "pres"), "linux_pres")
        self.assertEqual(mkinitcpio.file_name("5.14", "nom"), "linux-lts_nom")

    def test__display_name(self):
        mkinitcpio = Mkinitcpio(distribution_mock())
        self.assertEqual(mkinitcpio.display_name("5.19", "my_preset"),
                         "Arch Linux (my_preset)")
        self.assertEqual(mkinitcpio.display_name("5.14", "set"),
                         "Arch Linux lts (set)")

    def test__build_initramfs_with_microcode(self):
        preset_info = "some info\npreset_image = /test\nsome more info\nx=y\n"

        def read(file):
            if file == Path("/etc/mkinitcpio.d/linux-lts.preset"):
                return preset_info
            raise ValueError(file)

        base = "verity_squash_root.initramfs.mkinitcpio"
        all_mocks = mock.Mock()
        all_mocks.read_text_from.side_effect = read
        with (mock.patch("{}.merge_initramfs_images".format(base),
                         new=all_mocks.merge_initramfs_images),
              mock.patch("{}.exec_binary".format(base),
                         new=all_mocks.exec_binary),
              mock.patch("{}.read_text_from".format(base),
                         new=all_mocks.read_text_from),
              mock.patch("{}.write_str_to".format(base),
                         new=all_mocks.write_str_to)):
            distri_mock = distribution_mock()
            mkinitcpio = Mkinitcpio(distri_mock)
            res = mkinitcpio.build_initramfs_with_microcode(
                "5.14", "x_preset")
            base_name = "linux-lts-x_preset"
            call = mock.call
            self.assertEqual(
                all_mocks.mock_calls,
                [call.read_text_from(
                     Path("/etc/mkinitcpio.d/linux-lts.preset")),
                 call.write_str_to(
                     TMPDIR / "linux-lts-x_preset.preset",
                     ("{}\nPRESETS=('x_preset')\n"
                      "x_preset_image={}/{}.initcpio\n".format(
                          preset_info, TMPDIR, base_name))),
                 call.exec_binary(["mkinitcpio", "-p",
                                   "{}/{}.preset".format(TMPDIR, base_name)]),
                 call.merge_initramfs_images(TMPDIR / "{}.initcpio".format(
                                                 base_name),
                                             distri_mock.microcode_paths(),
                                             TMPDIR / "{}.image".format(
                                                 base_name))])
            self.assertEqual(res, TMPDIR / "{}.image".format(base_name))

    @mock.patch("verity_squash_root.initramfs.mkinitcpio.exec_binary")
    def test__list_kernel_presets(self, exec_mock):
        def change_lib_path(cmd):
            cmd[0] = str(PROJECT_ROOT / cmd[0].strip('/'))
            cmd[1] = "../..{}".format(
                TEST_FILES_DIR / "linux_name")
            return exec_binary(cmd)

        exec_mock.side_effect = change_lib_path
        mkinitcpio = Mkinitcpio(distribution_mock())
        result = mkinitcpio.list_kernel_presets("5.14")
        self.assertEqual(result, ["default", "fallback", "test"])
        exec_mock.assert_called_once_with([
            str(PROJECT_ROOT /
                'usr/lib/verity-squash-root/mkinitcpio_list_presets'),
            "../..{}".format(
                PROJECT_ROOT /
                'tests/unit/files/distributions/arch/linux_name')])
