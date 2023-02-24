import unittest
from unittest import mock
from verity_squash_root.distributions.autodetect import load_os_release, \
    autodetect_distribution
from tests.unit.test_helper import get_test_files_path


TEST_FILES_DIR = get_test_files_path("distributions")


class DistributionDetectTest(unittest.TestCase):

    @mock.patch("verity_squash_root.distributions.autodetect.ETC_FILE",
                new=TEST_FILES_DIR / "etc-os-release")
    def test__load_os_release__etc(self):
        result = load_os_release()
        self.assertEqual(result,
                         {"ID": "arch",
                          "NAME": "Arch Linux",
                          "HOME_URL": "arch website",
                          "LOGO": "archlinux-logo",
                          })

    @mock.patch("verity_squash_root.distributions.autodetect.ETC_FILE")
    @mock.patch("verity_squash_root.distributions.autodetect.USR_FILE",
                new=TEST_FILES_DIR / "usr-os-release")
    def test__load_os_release__usr(self, file):
        file.resolve.return_value.is_file.return_value = False
        result = load_os_release()
        self.assertEqual(result,
                         {"ID": "ubuntu",
                          "ID_LIKE": "debian",
                          "NAME": "Debian GNU/Linux",
                          "HOME_URL": "their site",
                          })

    @mock.patch("verity_squash_root.distributions.autodetect.ETC_FILE",
                new=TEST_FILES_DIR / "arch")
    @mock.patch("verity_squash_root.distributions.autodetect.ArchLinuxConfig")
    def test__autodetect_distribution__arch(self, mock):
        result = autodetect_distribution()
        mock.assert_called_once_with("arch", "My Arch")
        self.assertEqual(result, mock())

    @mock.patch("verity_squash_root.distributions.autodetect.ETC_FILE",
                new=TEST_FILES_DIR / "debian")
    @mock.patch("verity_squash_root.distributions.autodetect.DebianConfig")
    def test__autodetect_distribution__debian(self, mock):
        result = autodetect_distribution()
        mock.assert_called_once_with("debian", "Debian GNU/Linux")
        self.assertEqual(result, mock())

    @mock.patch("verity_squash_root.distributions.autodetect.ETC_FILE",
                new=TEST_FILES_DIR / "debian-like")
    @mock.patch("verity_squash_root.distributions.autodetect.DebianConfig")
    def test__autodetect_distribution__debian_like(self, mock):
        result = autodetect_distribution()
        mock.assert_called_once_with("ubuntu", "Ubuntu 22.04")
        self.assertEqual(result, mock())
