import unittest
from tests.unit.efi import EfiTest


def test_suite():
    suite = unittest.TestSuite([
        unittest.makeSuite(EfiTest),
    ])
    return suite
