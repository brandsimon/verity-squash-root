from typing import Generator, List, Tuple
from configparser import ConfigParser
from verity_squash_root.config import config_str_to_stripped_arr
from verity_squash_root.distributions.base import DistributionConfig
from verity_squash_root.initramfs.base import InitramfsBuilder, \
    iterate_distribution_efi

BACKUP_SUFFIX = "_backup"


def backup_file(file: str) -> str:
    return "{}{}".format(file, BACKUP_SUFFIX)


def backup_label(label: str) -> str:
    return "{} Backup".format(label)


def tmpfs_file(file: str) -> str:
    return "{}_tmpfs".format(file)


def tmpfs_label(label: str) -> str:
    return "{} tmpfs".format(label)


def kernel_is_ignored(base_name: str, ignored: List[str]) -> bool:
    if base_name in ignored:
        return True
    if base_name.endswith(BACKUP_SUFFIX):
        length = len(BACKUP_SUFFIX)
        # Also ignore A_backup, when A is ignored
        if base_name[:-length] in ignored:
            return True
    return False


def iterate_kernel_variants(distribution: DistributionConfig,
                            initramfs: InitramfsBuilder) \
        -> Generator[Tuple[str, str, str, str], None, None]:
    for [kernel, preset, base_name] in iterate_distribution_efi(distribution,
                                                                initramfs):
        display = initramfs.display_name(kernel, preset)
        yield (kernel, preset, base_name, display)
        yield (kernel, preset, backup_file(base_name), backup_label(display))
        yield (kernel, preset, tmpfs_file(base_name), tmpfs_label(display))
        yield (kernel, preset,
               backup_file(tmpfs_file(base_name)),
               backup_label(tmpfs_label(display)))


def iterate_non_ignored_kernel_variants(
        config: ConfigParser, distribution: DistributionConfig,
        initramfs: InitramfsBuilder) -> Generator[Tuple[
            str, str, str, str], None, None]:
    ignore_efis = config_str_to_stripped_arr(
        config["DEFAULT"]["IGNORE_KERNEL_EFIS"])

    for (kernel, preset, base_name, display) in iterate_kernel_variants(
            distribution, initramfs):
        if not kernel_is_ignored(base_name, ignore_efis):
            yield (kernel, preset, base_name, display)
