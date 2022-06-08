import unittest
from secure_squash_root.file_names import iterate_kernel_variants
from tests.unit.distributions.base import distribution_mock


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
