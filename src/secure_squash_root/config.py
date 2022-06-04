import os
from configparser import ConfigParser


TMPDIR = "/tmp/secure_squash_root"
KERNEL_PARAM_BASE = "secure_squash_root"
CONFIG_FILE = "/etc/{}/config.ini".format(KERNEL_PARAM_BASE)


def str_to_exclude_dirs(s: str) -> [str]:
    return [i.strip() for i in s.split(",")]


def read_config() -> ConfigParser:
    config = ConfigParser()
    directory = os.path.dirname(__file__)
    defconfig = os.path.join(directory, "default_config.ini")
    config.read(defconfig)
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    return config
