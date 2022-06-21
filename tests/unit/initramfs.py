import os
import unittest
from .test_helper import wrap_tempdir
from verify_squash_root.file_op import write_str_to, read_text_from
from verify_squash_root.initramfs import merge_initramfs_images


class InitramfsTest(unittest.TestCase):

    @wrap_tempdir
    def test__merge_initramfs_images(self, tempdir):
        in1 = os.path.join(tempdir, "some_file")
        in2 = os.path.join(tempdir, "another_file")
        in3 = os.path.join(tempdir, "filename")
        in1_text = "First\npart"
        in2_text = "First \n part\n"
        in3_text = "Third part"
        for i in [(in1, in1_text),
                  (in2, in2_text),
                  (in3, in3_text)]:
            write_str_to(i[0], i[1])

        out = os.path.join(tempdir, "merged_file")
        merge_initramfs_images(in1, ["/not/existing", in2,
                                     "/no/image", "/still/no/image",
                                     in3, "another/non/image"],
                               out)
        self.assertEqual(read_text_from(out),
                         "{}{}{}".format(
                             in2_text, in3_text, in1_text))
