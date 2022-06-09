import os
import unittest
from unittest import mock
from tests.unit.test_helper import PROJECT_ROOT
from secure_squash_root.config import config_str_to_stripped_arr, \
    read_config, check_config, is_volatile_boot, check_config_and_system


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

    @mock.patch("secure_squash_root.config.os.path.ismount")
    def test__check_config(self, mount_mock):
        config = {
            "DEFAULT": {
                "ROOT_MOUNT": "/opt/root",
                "EFI_PARTITION": "/boot/efimnt",
            }
        }

        def run(mount_result):
            mount_mock.side_effect = mount_result
            result = check_config(config)
            self.assertEqual(
                mount_mock.mock_calls,
                [mock.call("/opt/root"),
                 mock.call("/boot/efimnt")])
            mount_mock.reset_mock()
            return result

        mnt_error = "Directory '/opt/root' is not a mount point"
        efi_error = "Directory '/boot/efimnt' is not a mount point"
        self.assertEqual(run([True, True]), [])
        self.assertEqual(run([True, False]), [efi_error])
        self.assertEqual(run([False, True]), [mnt_error])
        self.assertEqual(run([False, False]), [mnt_error, efi_error])

    @mock.patch("secure_squash_root.config.exec_binary")
    def test__is_volatile_boot(self, exec_mock):
        cmdline = ("rw,relatime,lowerdir=/secure-squashfs-tmp/squashroot,"
                   "upperdir={},workdir=/sysroot/workdir,"
                   "index=off,xino=off,metacopy=off")

        def test(upper, result):
            exec_mock.reset_mock()
            exec_mock.return_value = [cmdline.format(upper).encode(), b""]
            self.assertEqual(is_volatile_boot(), result)
            exec_mock.assert_called_once_with(
                ["findmnt", "-uno", "OPTIONS", "/"])

        test("/sysroot/overlay", False)
        test("/secure-squashfs-tmp/tmpfs/overlay", True)

    def test__check_config_and_system(self):
        with mock.patch("secure_squash_root.config.is_volatile_boot") as \
                is_vol, \
             mock.patch("secure_squash_root.config.check_config") as \
                check_config:
            check_config.return_value = ["some", "test", "values"]
            is_vol.return_value = True
            config = mock.Mock()
            res = check_config_and_system(config)
            is_vol.assert_called_once_with()
            check_config.assert_called_once_with(config)
            self.assertEqual(res, ["some", "test", "values"])

            is_vol.return_value = False
            res = check_config_and_system(config)
            self.assertEqual(
                res,
                ["some", "test", "values",
                 "System is not booted in volatile mode:",
                 " - System could be compromised from previous boots",
                 (" - It is recommended to enter secure boot key passwords "
                  "only in volatile mode"),
                 " - Know what you are doing!"])
