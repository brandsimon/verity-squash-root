import unittest
from tests.unit.distributions.base import distribution_mock
from secure_squash_root.file_names import iterate_kernel_variants, \
    backup_file, backup_label, tmpfs_file, tmpfs_label


class FileNamesTest(unittest.TestCase):

    def test__iterate_kernel_variants(self):
        distri_mock = distribution_mock()
        variants = list(iterate_kernel_variants(distri_mock))
        self.assertEqual(
            variants,
            [('5.19', 'default', 'linux_default', 'Distri Linux (default)'),
             ('5.19', 'default', 'linux_default_backup',
              'Distri Linux (default) Backup'),
             ('5.19', 'default', 'linux_default_tmpfs',
              'Distri Linux (default) tmpfs'),
             ('5.19', 'default', 'linux_default_tmpfs_backup',
              'Distri Linux (default) tmpfs Backup'),
             ('5.19', 'fallback', 'linux_fallback', 'Distri Linux (fallback)'),
             ('5.19', 'fallback', 'linux_fallback_backup',
              'Distri Linux (fallback) Backup'),
             ('5.19', 'fallback', 'linux_fallback_tmpfs',
              'Distri Linux (fallback) tmpfs'),
             ('5.19', 'fallback', 'linux_fallback_tmpfs_backup',
              'Distri Linux (fallback) tmpfs Backup'),
             ('5.14', 'default', 'linux-lts_default',
              'Distri Linux-lts (default)'),
             ('5.14', 'default', 'linux-lts_default_backup',
              'Distri Linux-lts (default) Backup'),
             ('5.14', 'default', 'linux-lts_default_tmpfs',
              'Distri Linux-lts (default) tmpfs'),
             ('5.14', 'default', 'linux-lts_default_tmpfs_backup',
              'Distri Linux-lts (default) tmpfs Backup')])

    def test__backup_file(self):
        self.assertEqual(backup_file("linux-lts"), "linux-lts_backup")

    def test__backup_label(self):
        self.assertEqual(backup_label("Linux LTS"), "Linux LTS Backup")

    def test__tmpfs_file(self):
        self.assertEqual(tmpfs_file("linux-lts"), "linux-lts_tmpfs")

    def test__tmpfs_label(self):
        self.assertEqual(tmpfs_label("Linux LTS"), "Linux LTS tmpfs")
