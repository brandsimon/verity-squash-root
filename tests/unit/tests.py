import unittest
from tests.unit.cmdline import CmdlineTest
from tests.unit.config import ConfigTest
from tests.unit.distributions.arch import ArchLinuxConfigTest
from tests.unit.distributions.base import BaseDistributionTest
from tests.unit.efi import EfiTest
from tests.unit.exec import ExecTest
from tests.unit.file_op import FileOPTest
from tests.unit.image import ImageTest
from tests.unit.initramfs import InitramfsTest
from tests.unit.parsing import ParsingTest
from tests.unit.pep_checker import Pep8Test


def test_suite():
    suite = unittest.TestSuite([
        unittest.makeSuite(ArchLinuxConfigTest),
        unittest.makeSuite(BaseDistributionTest),
        unittest.makeSuite(CmdlineTest),
        unittest.makeSuite(ConfigTest),
        unittest.makeSuite(EfiTest),
        unittest.makeSuite(ExecTest),
        unittest.makeSuite(FileOPTest),
        unittest.makeSuite(ImageTest),
        unittest.makeSuite(InitramfsTest),
        unittest.makeSuite(ParsingTest),
        unittest.makeSuite(Pep8Test),
    ])
    return suite
