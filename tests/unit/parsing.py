import unittest
from verify_squash_root.parsing import info_to_dict


class ParsingTest(unittest.TestCase):

    def test__info_to_dict(self):
        text = ("Somekey = Somevalue\n# comment\nRandom line\n"
                "Anotherkey = Anothervalue\nMore random lines\n"
                "Var = Val\nTest = 1\nVar = Overwritten\n")
        result = info_to_dict(text, "=")
        self.assertEqual(result,
                         {"Somekey": "Somevalue",
                          "Anotherkey": "Anothervalue",
                          "Test": "1",
                          "Var": "Overwritten"})

        self.assertEqual(info_to_dict("Var: val"),
                         {"Var": "val"})
