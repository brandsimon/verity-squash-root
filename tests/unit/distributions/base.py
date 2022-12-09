import unittest
from pathlib import Path
from unittest import mock
from verity_squash_root.distributions.base import \
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


class BaseDistributionTest(unittest.TestCase):

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
