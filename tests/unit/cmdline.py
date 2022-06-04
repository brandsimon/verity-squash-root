import unittest
from secure_squash_root.cmdline import current_slot, unused_slot


class CmdlineTest(unittest.TestCase):

    def test__current_slot(self):
        self.assertEqual(
            current_slot("root=L=5 rw secure_squash_root_slot=a pti=on"),
            "a")
        self.assertEqual(
            current_slot("crpytroot secure_squash_root_slot=b tsx=off"),
            "b")
        self.assertEqual(
            current_slot("crpytroot pti=on tsx=off"),
            None)

    def test__unused_slot(self):
        self.assertEqual(
            unused_slot("root=L=5 rw secure_squash_root_slot=a pti=on"),
            "b")
        self.assertEqual(
            unused_slot("crpytroot secure_squash_root_slot=b tsx=off"),
            "a")
        self.assertEqual(
            unused_slot("crpytroot pti=on tsx=off"),
            "a")
