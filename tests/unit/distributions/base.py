import unittest
from pathlib import Path
from unittest import mock
from verity_squash_root.distributions.base import iterate_distribution_efi, \
    calc_kernel_packages_not_unique


def distribution_mock():
    obj_kernel = {"5.19": "linux", "5.14": "linux-lts"}

    def vmlinuz(kernel):
        return Path("/lib64/modules/{}/vmlinuz".format(kernel))

    def kernel_to_name(kernel):
        return obj_kernel[kernel]

    distri_mock = mock.Mock()
    distri_mock.list_kernels.return_value = ["5.19", "5.14"]
    distri_mock.efi_dirname.return_value = "ArchEfi"
    distri_mock.display_name.return_value = "Arch"
    distri_mock.vmlinuz.side_effect = vmlinuz
    distri_mock.kernel_to_name.side_effect = kernel_to_name
    return distri_mock


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


class BaseDistributionTest(unittest.TestCase):

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

    def test__calc_kernel_packages_not_unique(self):
        distri_mock = distribution_mock()
        self.assertEqual(
            [],
            calc_kernel_packages_not_unique(distri_mock))

        distri_mock.kernel_to_name.side_effect = None
        distri_mock.kernel_to_name.return_value = "linux-h"
        self.assertEqual(
            ["Package linux-h has multiple kernel versions: 5.14, 5.19",
             "This means, that there are probably old files in "
             "/usr/lib/modules"],
            calc_kernel_packages_not_unique(distri_mock))
