import unittest
from tests.unit.efi import EfiTest
from tests.unit.exec import ExecTest
from tests.unit.pep_checker import Pep8Test


def test_suite():
    suite = unittest.TestSuite([
        unittest.makeSuite(EfiTest),
        unittest.makeSuite(ExecTest),
        unittest.makeSuite(Pep8Test),
    ])
    return suite
