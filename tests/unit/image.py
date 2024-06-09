import unittest
from pathlib import Path
from unittest import mock
from verity_squash_root.image import mksquashfs, veritysetup_image, \
    verity_image_path
from .test_helper import PROJECT_ROOT


class ImageTest(unittest.TestCase):

    @mock.patch("verity_squash_root.image.exec_binary")
    def test__veritysetup_image(self, mock):
        mock.return_value = (b'Test: 5\nRoot hash: 0x1256890\nLine', b'')
        root_hash = veritysetup_image(Path("/myimage.squashfs"))
        self.assertEqual(root_hash, "0x1256890")
        mock.assert_called_once_with(
            ["veritysetup", "format", "/myimage.squashfs",
             "/myimage.squashfs.verity"])

    def test__verity_image_path(self):
        self.assertEqual(verity_image_path(Path("/mnt/root/my_img.iso")),
                         Path("/mnt/root/my_img.iso.verity"))

    @mock.patch("verity_squash_root.image.exec_binary")
    def test__mksquashfs(self, mock):
        setup = str(PROJECT_ROOT / "setup.py")
        mksquashfs(["var/!(lib)", "/home", setup, "/root"], "/image.squashfs",
                   "/mnt/root/", "/boot/weird/efi")
        mock.assert_called_once_with(
            ['mksquashfs', '/', '/image.squashfs',
             '-reproducible', '-xattrs', '-wildcards', '-noappend',
             '-no-exports',
             '-p', '/mnt/root/ d 0700 0 0',
             '-p', '/boot/weird/efi d 0700 0 0',
             '-e', 'dev/*', 'dev/.*',
             'proc/*', 'proc/.*', 'run/*', 'run/.*', 'sys/*', 'sys/.*',
             'tmp/*', 'tmp/.*', 'mnt/root/*', 'mnt/root/.*',
             'boot/weird/efi/*', 'boot/weird/efi/.*',
             'var/!(lib)/*', 'var/!(lib)/.*',
             'home/*', 'home/.*',
             setup[1:],
             'root/*', 'root/.*'])
