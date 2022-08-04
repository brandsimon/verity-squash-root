import unittest
from pathlib import Path
from unittest import mock
from tests.unit.test_helper import PROJECT_ROOT
from verify_squash_root.config import config_str_to_stripped_arr, \
    read_config, check_config, is_volatile_boot, check_config_and_system


class ConfigTest(unittest.TestCase):

    def test__config_str_to_stripped_arr(self):
        self.assertEqual(
            config_str_to_stripped_arr(
                " var/!(lib) ,/mnt/test\n,another/dir/ ,testdir"),
            ["var/!(lib)", "/mnt/test", "another/dir/", "testdir"])

    @mock.patch("verify_squash_root.config.ConfigParser")
    def test__read_config(self, cp_mock):
        result = read_config()
        cp_mock.assert_called_once_with()
        self.assertEqual(cp_mock.mock_calls, [
            mock.call(),
            mock.call().read(
                PROJECT_ROOT / "src/verify_squash_root/default_config.ini"),
            mock.call().read(
                Path('/usr/share/verify_squash_root/default.ini')),
            mock.call().read(Path('/etc/verify_squash_root/config.ini'))])
        self.assertEqual(result, cp_mock())

    @mock.patch("verify_squash_root.config.Path")
    def test__check_config(self, path_mock):
        config = {
            "DEFAULT": {
                "ROOT_MOUNT": "/opt/root",
                "EFI_PARTITION": "/boot/efimnt",
            }
        }

        def run(mount_result):
            root_mock = mock.Mock()
            root_mock.is_mount.return_value = mount_result[0]
            efi_mock = mock.Mock()
            efi_mock.is_mount.return_value = mount_result[1]

            def ret_mock(name):
                pm = mock.Mock()
                pm.resolve.return_value = \
                    root_mock if name == "/opt/root" else efi_mock
                pm.__str__ = mock.Mock()
                pm.__str__.return_value = name
                return pm

            path_mock.side_effect = ret_mock
            result = check_config(config)
            self.assertEqual(
                path_mock.mock_calls,
                [mock.call("/opt/root"),
                 mock.call("/boot/efimnt")])
            path_mock.reset_mock()
            return result

        mnt_error = "Directory '/opt/root' is not a mount point"
        efi_error = "Directory '/boot/efimnt' is not a mount point"
        self.assertEqual(run([True, True]), [])
        self.assertEqual(run([True, False]), [efi_error])
        self.assertEqual(run([False, True]), [mnt_error])
        self.assertEqual(run([False, False]), [mnt_error, efi_error])

    @mock.patch("verify_squash_root.config.exec_binary")
    def test__is_volatile_boot(self, exec_mock):
        cmdline = ("rw,relatime,lowerdir=/verify-squashfs-tmp/squashroot,"
                   "upperdir={},workdir=/sysroot/workdir,"
                   "index=off,xino=off,metacopy=off")

        def test(upper, result):
            exec_mock.reset_mock()
            exec_mock.return_value = [cmdline.format(upper).encode(), b""]
            self.assertEqual(is_volatile_boot(), result)
            exec_mock.assert_called_once_with(
                ["findmnt", "-uno", "OPTIONS", "/"])

        test("/sysroot/overlay", False)
        test("/verify-squashfs-tmp/tmpfs/overlay", True)

    def test__check_config_and_system(self):
        base = "verify_squash_root.config"
        with (mock.patch("{}.is_volatile_boot".format(base)) as is_vol,
              mock.patch("{}.check_config".format(base)) as check_config):
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
