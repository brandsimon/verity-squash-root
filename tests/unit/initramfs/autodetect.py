import unittest
from unittest import mock
from verity_squash_root.initramfs.autodetect import autodetect_initramfs


class InitramfsDetectTest(unittest.TestCase):

    @mock.patch("verity_squash_root.initramfs.autodetect.shutil")
    @mock.patch("verity_squash_root.initramfs.autodetect.Mkinitcpio")
    def test__autodetect__mkinitcpio(self, mkinitcpio_mock, shutil_mock):
        distri = mock.Mock()
        shutil_mock.which.return_value = True
        result = autodetect_initramfs(distri)
        shutil_mock.which.assert_called_once_with("mkinitcpio")
        mkinitcpio_mock.assert_called_once_with(distri)
        self.assertEqual(result, mkinitcpio_mock())

    @mock.patch("verity_squash_root.initramfs.autodetect.shutil")
    @mock.patch("verity_squash_root.initramfs.autodetect.Dracut")
    def test__autodetect__dracut(self, dracut_mock, shutil_mock):
        def which(f):
            if f == "dracut":
                return f
            return None

        distri = mock.Mock()
        shutil_mock.which.side_effect = which
        result = autodetect_initramfs(distri)
        self.assertEqual(shutil_mock.which.mock_calls,
                         [mock.call("mkinitcpio"),
                          mock.call("dracut")])
        dracut_mock.assert_called_once_with(distri)
        self.assertEqual(result, dracut_mock())

    @mock.patch("verity_squash_root.initramfs.autodetect.shutil")
    def test__autodetect__unkown(self, shutil_mock):
        shutil_mock.which.return_value = None
        with self.assertRaises(ValueError) as e:
            autodetect_initramfs(mock.Mock())
        self.assertEqual(str(e.exception),
                         "No supported initramfs builder found")
