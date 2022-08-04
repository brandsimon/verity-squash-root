import unittest
from pathlib import Path
from .test_helper import wrap_tempdir
from verify_squash_root.file_op import write_str_to, read_text_from
from verify_squash_root.initramfs import merge_initramfs_images


class InitramfsTest(unittest.TestCase):

    @wrap_tempdir
    def test__merge_initramfs_images(self, tempdir):
        in1 = tempdir / "some_file"
        in2 = tempdir / "another_file"
        in3 = tempdir / "filename"
        in1_text = "First\npart"
        in2_text = "First \n part\n"
        in3_text = "Third part"
        for i in [(in1, in1_text),
                  (in2, in2_text),
                  (in3, in3_text)]:
            write_str_to(i[0], i[1])

        out = tempdir / "merged_file"
        merge_initramfs_images(in1, [Path("/not/existing"), in2,
                                     Path("/no/image"),
                                     Path("/still/no/image"),
                                     in3,
                                     Path("another/non/image")],
                               out)
        self.assertEqual(read_text_from(out),
                         "{}{}{}".format(
                             in2_text, in3_text, in1_text))
