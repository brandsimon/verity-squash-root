import unittest
from tests.unit.cmdline import CmdlineTest
from tests.unit.config import ConfigTest
from tests.unit.decrypt import DecryptTest
from tests.unit.distributions.arch import ArchLinuxConfigTest
from tests.unit.distributions.base import BaseDistributionTest
from tests.unit.efi import EfiTest
from tests.unit.encrypt import EncryptTest
from tests.unit.exec import ExecTest
from tests.unit.file_names import FileNamesTest
from tests.unit.file_op import FileOPTest
from tests.unit.image import ImageTest
from tests.unit.initramfs import InitramfsTest
from tests.unit.initramfs.dracut import DracutTest
from tests.unit.main import MainTest
from tests.unit.mount import MountTest
from tests.unit.parsing import ParsingTest
from tests.unit.pep_checker import Pep8Test
from tests.unit.setup import SetupTest


def test_suite():
    suite = unittest.TestSuite([
        unittest.makeSuite(ArchLinuxConfigTest),
        unittest.makeSuite(BaseDistributionTest),
        unittest.makeSuite(CmdlineTest),
        unittest.makeSuite(ConfigTest),
        unittest.makeSuite(DracutTest),
        unittest.makeSuite(DecryptTest),
        unittest.makeSuite(EfiTest),
        unittest.makeSuite(EncryptTest),
        unittest.makeSuite(ExecTest),
        unittest.makeSuite(FileNamesTest),
        unittest.makeSuite(FileOPTest),
        unittest.makeSuite(ImageTest),
        unittest.makeSuite(InitramfsTest),
        unittest.makeSuite(MainTest),
        unittest.makeSuite(MountTest),
        unittest.makeSuite(ParsingTest),
        unittest.makeSuite(Pep8Test),
        unittest.makeSuite(SetupTest),
    ])
    return suite
