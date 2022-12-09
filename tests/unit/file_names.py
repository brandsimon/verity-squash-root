import unittest
from tests.unit.distributions.base import distribution_mock
from tests.unit.initramfs import create_initramfs_mock
from verity_squash_root.file_names import iterate_kernel_variants, \
    backup_file, backup_label, tmpfs_file, tmpfs_label, \
    iterate_non_ignored_kernel_variants, kernel_is_ignored


class FileNamesTest(unittest.TestCase):

    def test__iterate_kernel_variants(self):
        distri_mock = distribution_mock()
        initramfs_mock = create_initramfs_mock(distri_mock)
        variants = list(iterate_kernel_variants(distri_mock, initramfs_mock))
        self.assertEqual(
            variants,
            [('5.19', 'default', 'linux_default', 'Display Linux (default)'),
             ('5.19', 'default', 'linux_default_backup',
              'Display Linux (default) Backup'),
             ('5.19', 'default', 'linux_default_tmpfs',
              'Display Linux (default) tmpfs'),
             ('5.19', 'default', 'linux_default_tmpfs_backup',
              'Display Linux (default) tmpfs Backup'),
             ('5.19', 'fallback', 'linux_fallback',
              'Display Linux (fallback)'),
             ('5.19', 'fallback', 'linux_fallback_backup',
              'Display Linux (fallback) Backup'),
             ('5.19', 'fallback', 'linux_fallback_tmpfs',
              'Display Linux (fallback) tmpfs'),
             ('5.19', 'fallback', 'linux_fallback_tmpfs_backup',
              'Display Linux (fallback) tmpfs Backup'),
             ('5.14', 'default', 'linux-lts_default',
              'Display Linux-lts (default)'),
             ('5.14', 'default', 'linux-lts_default_backup',
              'Display Linux-lts (default) Backup'),
             ('5.14', 'default', 'linux-lts_default_tmpfs',
              'Display Linux-lts (default) tmpfs'),
             ('5.14', 'default', 'linux-lts_default_tmpfs_backup',
              'Display Linux-lts (default) tmpfs Backup')])

    def test__iterate_non_ignored_kernel_variants(self):
        distri_mock = distribution_mock()
        initramfs_mock = create_initramfs_mock(distri_mock)
        ignore = (" linux-lts_default_backup,linux_default_backup,"
                  "linux-lts_default_tmpfs ,linux_fallback")
        config = {
            "DEFAULT": {
                "IGNORE_KERNEL_EFIS": ignore,
            }
        }
        variants = list(iterate_non_ignored_kernel_variants(
            config, distri_mock, initramfs_mock))
        self.assertEqual(
            variants,
            [('5.19', 'default', 'linux_default', 'Display Linux (default)'),
             ('5.19', 'default', 'linux_default_tmpfs',
              'Display Linux (default) tmpfs'),
             ('5.19', 'default', 'linux_default_tmpfs_backup',
              'Display Linux (default) tmpfs Backup'),
             ('5.19', 'fallback', 'linux_fallback_tmpfs',
              'Display Linux (fallback) tmpfs'),
             ('5.19', 'fallback', 'linux_fallback_tmpfs_backup',
              'Display Linux (fallback) tmpfs Backup'),
             ('5.14', 'default', 'linux-lts_default',
              'Display Linux-lts (default)')])

    def test__backup_file(self):
        self.assertEqual(backup_file("linux-lts"), "linux-lts_backup")

    def test__backup_label(self):
        self.assertEqual(backup_label("Linux LTS"), "Linux LTS Backup")

    def test__tmpfs_file(self):
        self.assertEqual(tmpfs_file("linux-lts"), "linux-lts_tmpfs")

    def test__tmpfs_label(self):
        self.assertEqual(tmpfs_label("Linux LTS"), "Linux LTS tmpfs")

    def test__kernel_is_ignored(self):
        ignored = ["linux_fallback_tmpfs", "linux_default_backup",
                   "linux-lts_tmpfs"]
        self.assertEqual(kernel_is_ignored("linux_default", ignored),
                         False)
        self.assertEqual(kernel_is_ignored("linux_default_backup", ignored),
                         True)
        self.assertEqual(kernel_is_ignored("linux-lts_tmpfs_backup", ignored),
                         True)
