import unittest
from unittest import mock
from secure_squash_root import move_kernel_to


class MainTest(unittest.TestCase):

    def test__move_kernel_to(self):
        base = "secure_squash_root"
        call = mock.call
        all_mocks = mock.Mock()

        with mock.patch("{}.os".format(base),
                        new=all_mocks.os), \
             mock.patch("{}.shutil".format(base),
                        new=all_mocks.shutil), \
             mock.patch("{}.efi".format(base),
                        new=all_mocks.efi):
            # Kernel does not exist yet
            all_mocks.os.path.exists.return_value = False
            move_kernel_to("/tmp/test.efi",
                           "/boot/efi/EFI/linux.efi",
                           "a",
                           "/boot/efi/EFI/linux_backup.efi")
            self.assertEqual(
                all_mocks.mock_calls,
                [call.os.path.exists("/boot/efi/EFI/linux.efi"),
                 call.shutil.move("/tmp/test.efi", "/boot/efi/EFI/linux.efi")])

            all_mocks.reset_mock()
            # Kernel exist, backup not supplied
            all_mocks.os.path.exists.return_value = True
            move_kernel_to("/tmp/dir/linux.efi",
                           "/boot/efi/EFI/linux-lts.efi",
                           "a",
                           None)
            self.assertEqual(
                all_mocks.mock_calls,
                [call.os.path.exists("/boot/efi/EFI/linux-lts.efi"),
                 call.efi.file_matches_slot(
                     "/boot/efi/EFI/linux-lts.efi", "a"),
                 call.os.unlink("/boot/efi/EFI/linux-lts.efi"),
                 call.shutil.move("/tmp/dir/linux.efi",
                                  "/boot/efi/EFI/linux-lts.efi")])

            all_mocks.reset_mock()
            # Kernel exist, slot does not match
            all_mocks.os.path.exists.return_value = True
            all_mocks.efi.file_matches_slot.return_value = False
            move_kernel_to("/tmp/dir/tmp.efi",
                           "/boot/efi/EFI/linux_fb.efi",
                           "b",
                           "/boot/efi/EFI/linux_fb_backup2.efi")
            self.assertEqual(
                all_mocks.mock_calls,
                [call.os.path.exists("/boot/efi/EFI/linux_fb.efi"),
                 call.efi.file_matches_slot(
                     "/boot/efi/EFI/linux_fb.efi", "b"),
                 call.os.rename("/boot/efi/EFI/linux_fb.efi",
                                "/boot/efi/EFI/linux_fb_backup2.efi"),
                 call.shutil.move("/tmp/dir/tmp.efi",
                                  "/boot/efi/EFI/linux_fb.efi")])

            all_mocks.reset_mock()
            # Kernel exist, slot matches
            all_mocks.os.path.exists.return_value = True
            all_mocks.efi.file_matches_slot.return_value = True
            move_kernel_to("/tmp/tmp_a5.efi",
                           "/boot/efi/linux_test.efi",
                           "a",
                           "/boot/efi/EFI/linux_test_backup.efi")
            print(all_mocks.mock_calls)
            self.assertEqual(
                all_mocks.mock_calls,
                [call.os.path.exists("/boot/efi/linux_test.efi"),
                 call.efi.file_matches_slot(
                     "/boot/efi/linux_test.efi", "a"),
                 call.os.unlink("/boot/efi/linux_test.efi"),
                 call.shutil.move("/tmp/tmp_a5.efi",
                                  "/boot/efi/linux_test.efi")])
