import unittest
from unittest import mock
from unittest.mock import call
from verify_squash_root.decrypt import format_cmd, TAR_FILE, KEY_DIR, \
    decrypt_secure_boot_keys, DecryptKeys


class DecryptTest(unittest.TestCase):

    def test__format_cmd(self):
        self.assertEqual(format_cmd("\nage -d -o {}\n/etc/keys.tar.age",
                                    "/tmp/keys.tar"),
                         ["age", "-d", "-o", "/tmp/keys.tar",
                          "/etc/keys.tar.age"])

    def test__decrypt_secure_boot_keys(self):
        base = "verify_squash_root.decrypt"
        all_mocks = mock.MagicMock()
        with (mock.patch("{}.exec_binary".format(base),
                         new=all_mocks.exec_binary),
              mock.patch("{}.os".format(base),
                         new=all_mocks.os),
              mock.patch("{}.tarfile".format(base),
                         new=all_mocks.tarfile)):
            config = {
                "DEFAULT": {
                    "DECRYPT_SECURE_BOOT_KEYS_CMD": "cp /root/keys.tar {}",
                }
            }
            decrypt_secure_boot_keys(config)
            self.assertEqual(
                all_mocks.mock_calls,
                [call.os.mkdir(KEY_DIR),
                 call.exec_binary(["cp", "/root/keys.tar", TAR_FILE]),
                 call.tarfile.open(TAR_FILE),
                 call.tarfile.open().__enter__(),
                 call.tarfile.open().__enter__().extractall(KEY_DIR),
                 call.tarfile.open().__exit__(None, None, None)])

    def test__decrypt_keys(self):
        base = "verify_squash_root.decrypt"
        all_mocks = mock.Mock()
        config = mock.Mock()
        with (mock.patch("{}.decrypt_secure_boot_keys".format(base),
                         new=all_mocks.decrypt_secure_boot_keys),
              mock.patch("{}.shutil".format(base),
                         new=all_mocks.shutil)):
            with DecryptKeys(config):
                all_mocks.inner_func()
            self.assertEqual(
                all_mocks.mock_calls,
                [call.decrypt_secure_boot_keys(config),
                 call.inner_func(),
                 call.shutil.rmtree(KEY_DIR)])
