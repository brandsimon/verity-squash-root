from configparser import ConfigParser
from pathlib import Path
from typing import List
from verify_squash_root.exec import exec_binary


TMPDIR = Path("/tmp/verify_squash_root")
KEY_DIR = TMPDIR / "keys"
KERNEL_PARAM_BASE = "verify_squash_root"
CONFIG_FILE = Path("/etc/{}/config.ini".format(KERNEL_PARAM_BASE))
DISTRI_FILE = Path("/usr/share") / KERNEL_PARAM_BASE / "default.ini"
LOG_FILE = Path("/var/log/{}.log".format(KERNEL_PARAM_BASE))


def config_str_to_stripped_arr(s: str) -> List[str]:
    return [i.strip() for i in s.split(",")]


def read_config() -> ConfigParser:
    config = ConfigParser()
    directory = Path(__file__).resolve().parent
    defconfig = directory / "default_config.ini"
    config.read(defconfig)
    config.read(DISTRI_FILE)
    config.read(CONFIG_FILE)
    return config


def is_volatile_boot():
    res = exec_binary(["findmnt", "-uno", "OPTIONS", "/"])[0].decode()
    parts = res.split(",")
    return "upperdir=/verify-squashfs-tmp/tmpfs/overlay" in parts


def check_config(config: ConfigParser) -> List[str]:
    root_mount = Path(config["DEFAULT"]["ROOT_MOUNT"])
    efi_partition = Path(config["DEFAULT"]["EFI_PARTITION"])
    result = []
    for d in [root_mount, efi_partition]:
        if not d.resolve().is_mount():
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
