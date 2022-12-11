from configparser import ConfigParser
from pathlib import Path
from typing import List
from verity_squash_root.exec import exec_binary


TMPDIR = Path("/tmp/verity_squash_root")
KEY_DIR = TMPDIR / "keys"
KERNEL_PARAM_BASE = "verity_squash_root"
NAME_DASH = KERNEL_PARAM_BASE.replace("_", "-")
CONFIG_DIR = Path("/etc/{}".format(KERNEL_PARAM_BASE))
CONFIG_FILE = CONFIG_DIR / "config.ini"
DISTRI_FILE = Path("/usr/share") / KERNEL_PARAM_BASE / "default.ini"
LOG_FILE = Path("/var/log/{}.log".format(KERNEL_PARAM_BASE))
EFI_PATH = Path("EFI")
EFI_KERNELS = EFI_PATH / KERNEL_PARAM_BASE


def config_str_to_stripped_arr(s: str) -> List[str]:
    return [i.strip() for i in s.split(",")]


def read_config() -> ConfigParser:
    # defaults will be visible in EXTRA_SIGN and break
    config = ConfigParser(default_section="DO_NOT_USE_DEFAULTS")
    directory = Path(__file__).resolve().parent
    defconfig = directory / "default_config.ini"
    config.read(defconfig)
    config.read(DISTRI_FILE)
    config.read(CONFIG_FILE)
    return config


def is_volatile_boot():
    res = exec_binary(["findmnt", "-uno", "OPTIONS", "/"])[0].decode()
    parts = res.split(",")
    return "upperdir=/verity-squash-root-tmp/tmpfs/overlay" in parts


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
