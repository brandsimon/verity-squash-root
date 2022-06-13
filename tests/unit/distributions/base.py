import unittest
from unittest import mock
from secure_squash_root.distributions.base import iterate_distribution_efi, \
    calc_kernel_packages_not_unique


def distribution_mock():
    obj_kernel = {"5.19": "linux", "5.14": "linux-lts"}

    def list_kernel_presets(kernel):
        obj = {"5.19": ["default", "fallback"], "5.14": ["default"]}
        return obj[kernel]

    def file_name(kernel, preset):
        return "{}_{}".format(obj_kernel[kernel], preset)

    def display_name(kernel, preset):
        return "Distri {} ({})".format(obj_kernel[kernel].capitalize(), preset)

    def vmlinuz(kernel):
        return "/lib64/modules/{}/vmlinuz".format(kernel)

    distri_mock = mock.Mock()
    distri_mock.list_kernels.return_value = ["5.19", "5.14"]
    distri_mock.efi_dirname.return_value = "Arch"
    distri_mock.list_kernel_presets.side_effect = list_kernel_presets
    distri_mock.file_name.side_effect = file_name
    distri_mock.display_name.side_effect = display_name
    distri_mock.vmlinuz.side_effect = vmlinuz
    return distri_mock


class BaseDistributionTest(unittest.TestCase):

    def test__iterate_distribution_efi(self):
        distri_mock = distribution_mock()
        result = list(iterate_distribution_efi(distri_mock))
        self.assertEqual(result,
                         [("5.19", "default", "linux_default"),
                          ("5.19", "fallback", "linux_fallback"),
                          ("5.14", "default", "linux-lts_default")])
        self.assertEqual(distri_mock.mock_calls,
                         [mock.call.list_kernels(),
                          mock.call.list_kernel_presets("5.19"),
                          mock.call.file_name("5.19", "default"),
                          mock.call.file_name("5.19", "fallback"),
                          mock.call.list_kernel_presets("5.14"),
                          mock.call.file_name("5.14", "default")])

    def test__calc_kernel_packages_not_unique(self):
        distri_mock = distribution_mock()
        self.assertEqual(
            [],
            calc_kernel_packages_not_unique(distri_mock))

        distri_mock.file_name.side_effect = None
        distri_mock.file_name.return_value = "linux"
        self.assertEqual(
            ["Package linux has multiple kernel versions: 5.14, 5.19",
             "This means, that there are probably old files in "
             "/usr/lib/modules"],
            calc_kernel_packages_not_unique(distri_mock))
