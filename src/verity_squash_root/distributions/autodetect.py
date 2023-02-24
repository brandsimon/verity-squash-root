from collections.abc import Mapping
from pathlib import Path
from verity_squash_root.file_op import read_text_from
from verity_squash_root.distributions.arch import ArchLinuxConfig, \
    DistributionConfig
from verity_squash_root.distributions.debian import DebianConfig
import verity_squash_root.parsing as parsing

ETC_FILE = Path("/etc/os-release")
USR_FILE = Path("/usr/lib/os-release")


def load_os_release() -> Mapping[str, str]:
    if ETC_FILE.resolve().is_file():
        content = read_text_from(ETC_FILE)
    else:
        content = read_text_from(USR_FILE)
    info = parsing.info_to_dict(content, sep="=")
    result = {}
    for k, v in info.items():
        result[k] = v.strip('"')
    return result


def autodetect_distribution() -> DistributionConfig:
    info = load_os_release()
    os_id = info.get("ID", "")
    os_name = info.get("NAME", "")
    if os_id == "debian" or info.get("ID_LIKE") == "debian":
        return DebianConfig(os_id, os_name)
    elif info.get("ID") == "arch":
        return ArchLinuxConfig(os_id, os_name)
    else:
        raise ValueError(
            "Distribution {} not yet supported".format(info.get("ID")))
