import unittest
from unittest import mock
from secure_squash_root.distributions.base import iterate_distribution_efi


class BaseDistributionTest(unittest.TestCase):

    def test__iterate_distribution_efi(self):
        def list_kernels():
            return ["5.19", "5.14"]

        def list_kernel_presets(kernel):
            obj = {"5.19": ["default", "fallback"], "5.14": ["default"]}
            return obj[kernel]

        def file_name(kernel, preset):
            obj = {"5.19": "linux", "5.14": "linux-lts"}
            return "{}_{}".format(obj[kernel], preset)

        distri_mock = mock.Mock()
        distri_mock.list_kernels.side_effect = list_kernels
        distri_mock.list_kernel_presets.side_effect = list_kernel_presets
        distri_mock.file_name.side_effect = file_name
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
