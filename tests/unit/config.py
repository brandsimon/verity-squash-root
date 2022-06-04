import unittest
from secure_squash_root.config import str_to_exclude_dirs


class ConfigTest(unittest.TestCase):

    def test__str_to_exclude_dirs(self):
        self.assertEqual(
            str_to_exclude_dirs(
                " var/!(lib) ,/mnt/test\n,another/dir/ ,testdir"),
            ["var/!(lib)", "/mnt/test", "another/dir/", "testdir"])
