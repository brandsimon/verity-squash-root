import unittest
from unittest import mock
from secure_squash_root.image import mksquashfs, veritysetup_image


class ImageTest(unittest.TestCase):

    @mock.patch("secure_squash_root.image.exec_binary")
    def test__veritysetup_image(self, mock):
        mock.return_value = (b'Test: 5\nRoot hash: 0x1256890\nLine', b'')
        root_hash = veritysetup_image("/myimage.squashfs")
        self.assertEqual(root_hash, "0x1256890")
        mock.assert_called_once_with(
            ["veritysetup", "format", "/myimage.squashfs",
             "/myimage.squashfs.verity"])

    @mock.patch("secure_squash_root.image.exec_binary")
    def test__mksquashfs(self, mock):
        mksquashfs(["var/!(lib)", "/home", "/root"], "/image.squashfs",
                   "/mnt/root/", "/boot/wierd/efi")
        mock.assert_called_once_with(
            ['mksquashfs', '/', '/image.squashfs',
             '-reproducible', '-xattrs', '-wildcards', '-noappend',
             '-no-exports',
             '-p', '/mnt/root/ d 0700 0 0',
             '-p', '/boot/wierd/efi d 0700 0 0',
             '-e', 'dev/*', 'dev/.*',
             'proc/*', 'proc/.*', 'run/*', 'run/.*', 'sys/*', 'sys/.*',
             'tmp/*', 'tmp/.*', 'mnt/root/*', 'mnt/root/.*',
             'boot/wierd/efi/*', 'boot/wierd/efi/.*',
             'var/!(lib)/*', 'var/!(lib)/.*',
             'home/*', 'home/.*',
             'root/*', 'root/.*'])
