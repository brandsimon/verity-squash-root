import os
import unittest
from unittest import mock
from tests.unit.test_helper import PROJECT_ROOT
from secure_squash_root.config import config_str_to_stripped_arr, read_config


class ConfigTest(unittest.TestCase):

    def test__config_str_to_stripped_arr(self):
        self.assertEqual(
            config_str_to_stripped_arr(
                " var/!(lib) ,/mnt/test\n,another/dir/ ,testdir"),
            ["var/!(lib)", "/mnt/test", "another/dir/", "testdir"])

    @mock.patch("secure_squash_root.config.ConfigParser")
    def test__read_config(self, cp_mock):
        result = read_config()
        cp_mock.assert_called_once_with()
        self.assertEqual(cp_mock.mock_calls, [
            mock.call(),
            mock.call().read(
                os.path.join(PROJECT_ROOT,
                             "src/secure_squash_root/default_config.ini")),
            mock.call().read('/usr/share/secure_squash_root/default.ini'),
            mock.call().read('/etc/secure_squash_root/config.ini')])
        self.assertEqual(result, cp_mock())
