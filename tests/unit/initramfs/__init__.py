import unittest
from pathlib import Path
from unittest import mock
from verity_squash_root.file_op import write_str_to, read_text_from
from verity_squash_root.initramfs import merge_initramfs_images
from verity_squash_root.initramfs.base import iterate_distribution_efi
from tests.unit.distributions.base import distribution_mock
from tests.unit.test_helper import wrap_tempdir


def create_initramfs_mock(distri):
    initramfs_mock = mock.Mock()

    def file_name(kernel, preset):
        return "{}_{}".format(
            distri.kernel_to_name(kernel), preset)

    def display_name(kernel, preset):
        return "Display {} ({})".format(
            distri.kernel_to_name(kernel).capitalize(), preset)

    def list_kernel_presets(kernel):
        obj = {"5.19": ["default", "fallback"], "5.14": ["default"]}
        return obj[kernel]

    initramfs_mock.list_kernel_presets.side_effect = list_kernel_presets
    initramfs_mock.file_name.side_effect = file_name
    initramfs_mock.display_name.side_effect = display_name
    return initramfs_mock


class InitramfsTest(unittest.TestCase):

    @wrap_tempdir
    def test__merge_initramfs_images(self, tempdir):
        in1 = tempdir / "some_file"
        in2 = tempdir / "another_file"
        in3 = tempdir / "filename"
        in1_text = "First\npart"
        in2_text = "First \n part\n"
        in3_text = "Third part"
        for i in [(in1, in1_text),
                  (in2, in2_text),
                  (in3, in3_text)]:
            write_str_to(i[0], i[1])

        out = tempdir / "merged_file"
        merge_initramfs_images(in1, [Path("/not/existing"), in2,
                                     Path("/no/image"),
                                     Path("/still/no/image"),
                                     in3,
                                     Path("another/non/image")],
                               out)
        self.assertEqual(read_text_from(out),
                         "{}{}{}".format(
                             in2_text, in3_text, in1_text))

    def test__iterate_distribution_efi(self):
        distri_mock = distribution_mock()
        # create separate mock, since otherwise all_mock history will be full
        # with initramfs calls to distribution.
        initramfs_mock = create_initramfs_mock(distribution_mock())
        all_mock = mock.Mock()
        all_mock.distri = distri_mock
        all_mock.initramfs = initramfs_mock
        result = list(iterate_distribution_efi(distri_mock, initramfs_mock))
        self.assertEqual(result,
                         [("5.19", "default", "linux_default"),
                          ("5.19", "fallback", "linux_fallback"),
                          ("5.14", "default", "linux-lts_default")])
        self.assertEqual(all_mock.mock_calls,
                         [mock.call.distri.list_kernels(),
                          mock.call.initramfs.list_kernel_presets("5.19"),
                          mock.call.initramfs.file_name("5.19", "default"),
                          mock.call.initramfs.file_name("5.19", "fallback"),
                          mock.call.initramfs.list_kernel_presets("5.14"),
                          mock.call.initramfs.file_name("5.14", "default")])
