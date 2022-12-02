import unittest
from unittest import mock
from verity_squash_root.mount import TmpfsMount


class MountTest(unittest.TestCase):

    def test__tmpfs_mount(self):
        base = "verity_squash_root.mount"
        all_mocks = mock.Mock()
        all_mocks.path.__str__ = mock.Mock(return_value="/my_directory")
        with (mock.patch("{}.exec_binary".format(base),
                         new=all_mocks.exec_binary),
              mock.patch("{}.shutil".format(base),
                         new=all_mocks.shutil)):
            call = mock.call
            with TmpfsMount(all_mocks.path):
                self.assertEqual(
                    all_mocks.mock_calls[1:],
                    [call.path.mkdir(),
                     call.exec_binary(['mount', '-t', 'tmpfs', '-o',
                                       'mode=0700,uid=0,gid=0', 'tmpfs',
                                       '/my_directory'])])
                all_mocks.path.__str__.assert_called_once_with()
                all_mocks.reset_mock()
            self.assertEqual(
                all_mocks.mock_calls[1:],
                [call.exec_binary(['umount', '-f', '-R', '/my_directory']),
                 call.shutil.rmtree(all_mocks.path)])
            all_mocks.path.__str__.assert_called_once_with()
