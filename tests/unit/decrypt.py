import unittest
from unittest import mock
from unittest.mock import call
from verity_squash_root.decrypt import format_cmd, TAR_FILE, KEY_DIR, \
    decrypt_secure_boot_keys, DecryptKeys
from .test_helper import wrap_tempdir, get_test_files_path

TEST_FILES_DIR = get_test_files_path("decrypt")


class DecryptTest(unittest.TestCase):

    def test__format_cmd(self):
        self.assertEqual(format_cmd("\n\tage -d\t-o {}\n/etc/keys.tar.age",
                                    "/tmp/keys.tar"),
                         ["age", "-d", "-o", "/tmp/keys.tar",
                          "/etc/keys.tar.age"])

    @wrap_tempdir
    def test__decrypt_secure_boot_keys(self, tempdir):
        base = "verity_squash_root.decrypt"
        key_dir = tempdir / "keys"
        all_mocks = mock.MagicMock()
        with (mock.patch("{}.exec_binary".format(base),
                         new=all_mocks.exec_binary),
              mock.patch("{}.KEY_DIR".format(base),
                         new=key_dir),
              mock.patch("{}.tarfile".format(base),
                         new=all_mocks.tarfile)):
            config = {
                "DEFAULT": {
                    "DECRYPT_SECURE_BOOT_KEYS_CMD": "cp /root/keys.tar {}",
                }
            }
            self.assertEqual(key_dir.is_dir(), False)
            decrypt_secure_boot_keys(config)
            self.assertEqual(
                all_mocks.mock_calls,
                [call.exec_binary(["cp", "/root/keys.tar", str(TAR_FILE)]),
                 call.tarfile.open(TAR_FILE),
                 call.tarfile.open().__enter__(),
                 call.tarfile.open().__enter__().extract(
                     "db.crt", key_dir, filter='data'),
                 call.tarfile.open().__enter__().extract(
                     "db.key", key_dir, filter='data'),
                 call.tarfile.open().__exit__(None, None, None)])
            self.assertEqual(key_dir.is_dir(), True)

    def test__decrypt_keys(self):
        base = "verity_squash_root.decrypt"
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

    @wrap_tempdir
    def test__decrypt_keys__real_file(self, tempdir):
        cmd = "cp {} {{}}".format(TEST_FILES_DIR / "keys.tar")
        config = {
            "DEFAULT": {
                "DECRYPT_SECURE_BOOT_KEYS_CMD": cmd
            }
        }
        key_dir = tempdir / "keys"
        tar_file = key_dir / "keys.tar"
        base = "verity_squash_root.decrypt"
        with (mock.patch("{}.TAR_FILE".format(base),
                         new=tar_file),
              mock.patch("{}.KEY_DIR".format(base),
                         new=key_dir)):
            with DecryptKeys(config):
                key_file = key_dir / "db.key"
                cert_file = key_dir / "db.crt"
                self.assertEqual(
                    key_file.read_text(),
                    "DB Key File 842\n")
                self.assertEqual(
                    cert_file.read_text(),
                    "22 DB Cert File 7\n")
                # Test that no other file got extracted to avoid python
                # extract / extractall vulnerability
                self.assertEqual(
                    sorted(list(key_dir.iterdir())),
                    [cert_file, key_file, tar_file])
