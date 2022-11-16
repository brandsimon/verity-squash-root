import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import call
from verify_squash_root.encrypt import create_secure_boot_keys, \
    create_encrypted_tar_file, create_tar_file, \
    check_if_archives_exist, create_and_pack_secure_boot_keys, \
    PUBLIC_KEY_FILES_TAR, SIGNING_FILES_TAR, ALL_FILES_TAR, \
    SIGNING_FILES, PUBLIC_FILES, ALL_FILES
from .test_helper import wrap_tempdir


class EncryptTest(unittest.TestCase):

    @mock.patch("verify_squash_root.encrypt.exec_binary")
    def test__create_secure_boot_keys(self, mock):
        create_secure_boot_keys()
        mock.assert_called_once_with(
            ["/usr/lib/verify-squash-root/generate_secure_boot_keys"])

    @mock.patch("verify_squash_root.encrypt.exec_binary")
    def test__create_encrypted_tar_file(self, mock):
        create_encrypted_tar_file(
             ["db.key", "db.crt", "another_file", "/etc/resolv.conf"],
             "/etc/targetfile.tar.age")
        mock.assert_called_once_with(
            ["/usr/lib/verify-squash-root/create_encrypted_tar_file",
             "/etc/targetfile.tar.age",
             "db.key", "db.crt", "another_file", "/etc/resolv.conf"])

    def test__create_tar_file(self):
        base = "verify_squash_root.encrypt"
        all_mocks = mock.MagicMock()
        with mock.patch("{}.tarfile".format(base),
                        new=all_mocks.tarfile):
            target = Path("/etc/target/file.tar")
            create_tar_file(["file1", "db.key", "pk.crt", "/dev/null"],
                            target)
            self.assertEqual(
                all_mocks.mock_calls,
                [call.tarfile.open(target, "w"),
                 call.tarfile.open().__enter__(),
                 call.tarfile.open().__enter__().add("file1"),
                 call.tarfile.open().__enter__().add("db.key"),
                 call.tarfile.open().__enter__().add("pk.crt"),
                 call.tarfile.open().__enter__().add("/dev/null"),
                 call.tarfile.open().__exit__(None, None, None)])

    def test__check_if_archives_exist(self):
        base = "verify_squash_root.encrypt"
        all_mocks = mock.MagicMock()
        variants = [
            [False, False, False, None],
            [True, False, False, PUBLIC_KEY_FILES_TAR, all_mocks.pubkeytar],
            [False, True, False, SIGNING_FILES_TAR, all_mocks.signtar],
            [False, False, True, ALL_FILES_TAR, all_mocks.alltar]]
        for i in variants:
            with (mock.patch("{}.PUBLIC_KEY_FILES_TAR".format(base),
                             new=all_mocks.pubkeytar),
                  mock.patch("{}.SIGNING_FILES_TAR".format(base),
                             new=all_mocks.signtar),
                  mock.patch("{}.ALL_FILES_TAR".format(base),
                             new=all_mocks.alltar)):
                all_mocks.pubkeytar.exists.return_value = i[0]
                all_mocks.signtar.exists.return_value = i[1]
                all_mocks.alltar.exists.return_value = i[2]
                if i[3] is None:
                    check_if_archives_exist()
                else:
                    with self.assertRaises(ValueError) as e:
                        check_if_archives_exist()
                    self.assertEqual(
                        str(e.exception),
                        "Archive {} already exists, delete it only if "
                        "you dont need it anymore".format(i[4]))

    @wrap_tempdir
    def test__create_and_pack_secure_boot_keys(self, tempdir):
        base = "verify_squash_root.encrypt"
        all_mocks = mock.MagicMock()
        key_dir = tempdir / "keys"

        all_mocks = mock.MagicMock()
        with (mock.patch("{}.create_secure_boot_keys".format(base),
                         new=all_mocks.create_secure_boot_keys),
              mock.patch("{}.create_encrypted_tar_file".format(base),
                         new=all_mocks.create_encrypted_tar_file),
              mock.patch("{}.create_encrypted_tar_file".format(base),
                         new=all_mocks.create_encrypted_tar_file),
              mock.patch("{}.create_tar_file".format(base),
                         new=all_mocks.create_tar_file),
              mock.patch("{}.os".format(base),
                         new=all_mocks.os),
              mock.patch("{}.KEY_DIR".format(base),
                         new=key_dir)):

            cwd = Path.cwd()
            self.assertEqual(key_dir.is_dir(), False)
            create_and_pack_secure_boot_keys()
            self.assertEqual(
                all_mocks.mock_calls,
                [call.os.chdir(key_dir),
                 call.create_secure_boot_keys(),
                 call.create_encrypted_tar_file(SIGNING_FILES,
                                                SIGNING_FILES_TAR),
                 call.create_encrypted_tar_file(ALL_FILES, ALL_FILES_TAR),
                 call.create_tar_file(PUBLIC_FILES, PUBLIC_KEY_FILES_TAR),
                 call.os.chdir(cwd)])
            self.assertEqual(key_dir.is_dir(), True)

    @wrap_tempdir
    def test__create_and_pack_secure_boot_keys__error_cleanup(self, tempdir):
        base = "verify_squash_root.encrypt"
        all_mocks = mock.MagicMock()
        key_dir = tempdir / "keys"

        all_mocks = mock.MagicMock()
        with (mock.patch("{}.create_secure_boot_keys".format(base),
                         new=all_mocks.create_secure_boot_keys),
              mock.patch("{}.os".format(base),
                         new=all_mocks.os),
              mock.patch("{}.KEY_DIR".format(base),
                         new=key_dir)):

            cwd = Path.cwd()
            all_mocks.create_secure_boot_keys.side_effect = ValueError("")
            with self.assertRaises(ValueError):
                create_and_pack_secure_boot_keys()
            self.assertEqual(
                all_mocks.mock_calls,
                [call.os.chdir(key_dir),
                 call.create_secure_boot_keys(),
                 call.os.chdir(cwd)])
