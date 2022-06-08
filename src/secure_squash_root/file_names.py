from typing import Generator, Tuple
from configparser import ConfigParser
from secure_squash_root.config import config_str_to_stripped_arr
from secure_squash_root.distributions.base import DistributionConfig, \
    iterate_distribution_efi


def backup_file(file: str) -> str:
    return "{}_backup".format(file)


def backup_label(label: str) -> str:
    return "{} Backup".format(label)


def tmpfs_file(file: str) -> str:
    return "{}_tmpfs".format(file)


def tmpfs_label(label: str) -> str:
    return "{} tmpfs".format(label)


def iterate_kernel_variants(distribution: DistributionConfig) \
        -> Generator[Tuple[str, str, str, str], None, None]:
    for [kernel, preset, base_name] in iterate_distribution_efi(distribution):
        display = distribution.display_name(kernel, preset)
        yield (kernel, preset, base_name, display)
        yield (kernel, preset, backup_file(base_name), backup_label(display))
        yield (kernel, preset, tmpfs_file(base_name), tmpfs_label(display))
        yield (kernel, preset,
               backup_file(tmpfs_file(base_name)),
               backup_label(tmpfs_label(display)))


def iterate_non_ignored_kernel_variants(
        config: ConfigParser, distribution: DistributionConfig) \
        -> Generator[Tuple[str, str, str, str], None, None]:
    ignore_efis = config_str_to_stripped_arr(
        config["DEFAULT"]["IGNORE_KERNEL_EFIS"])

    for (kernel, preset, base_name, display) in iterate_kernel_variants(
            distribution):
        if base_name not in ignore_efis:
            yield (kernel, preset, base_name, display)
