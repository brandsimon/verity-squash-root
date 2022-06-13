import os
from configparser import ConfigParser
from typing import List
from secure_squash_root.exec import exec_binary


TMPDIR = "/tmp/secure_squash_root"
KEY_DIR = os.path.join(TMPDIR, "keys")
KERNEL_PARAM_BASE = "secure_squash_root"
CONFIG_FILE = "/etc/{}/config.ini".format(KERNEL_PARAM_BASE)
DISTRI_FILE = os.path.join("/usr/share/", KERNEL_PARAM_BASE, "default.ini")
LOG_FILE = "/var/log/{}.log".format(KERNEL_PARAM_BASE)


def config_str_to_stripped_arr(s: str) -> List[str]:
    return [i.strip() for i in s.split(",")]


def read_config() -> ConfigParser:
    config = ConfigParser()
    directory = os.path.dirname(__file__)
    defconfig = os.path.join(directory, "default_config.ini")
    config.read(defconfig)
    config.read(DISTRI_FILE)
    config.read(CONFIG_FILE)
    return config


def is_volatile_boot():
    res = exec_binary(["findmnt", "-uno", "OPTIONS", "/"])[0].decode()
    parts = res.split(",")
    return "upperdir=/secure-squashfs-tmp/tmpfs/overlay" in parts


def check_config(config: ConfigParser) -> List[str]:
    root_mount = config["DEFAULT"]["ROOT_MOUNT"]
    efi_partition = config["DEFAULT"]["EFI_PARTITION"]
    result = []
    for d in [root_mount, efi_partition]:
        if not os.path.ismount(d):
            result.append("Directory '{}' is not a mount point".format(d))
    return result


def check_config_and_system(config: ConfigParser) -> List[str]:
    res = check_config(config)
    if not is_volatile_boot():
        res.append("System is not booted in volatile mode:")
        res.append(" - System could be compromised from previous boots")
        res.append(" - It is recommended to enter secure boot key passwords "
                   "only in volatile mode")
        res.append(" - Know what you are doing!")
    return res
