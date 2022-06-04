import unittest
from tests.unit.efi import EfiTest
from tests.unit.exec import ExecTest
from tests.unit.file_op import FileOPTest
from tests.unit.image import ImageTest
from tests.unit.parsing import ParsingTest
from tests.unit.pep_checker import Pep8Test


def test_suite():
    suite = unittest.TestSuite([
        unittest.makeSuite(EfiTest),
        unittest.makeSuite(ExecTest),
        unittest.makeSuite(FileOPTest),
        unittest.makeSuite(ImageTest),
        unittest.makeSuite(ParsingTest),
        unittest.makeSuite(Pep8Test),
    ])
    return suite
