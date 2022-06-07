from typing import Generator, Tuple
from secure_squash_root.distributions.base import DistributionConfig, \
    iterate_distribution_efi


def iterate_kernel_variants(distribution: DistributionConfig) \
        -> Generator[Tuple[str, str, str, str], None, None]:
    for [kernel, preset, base_name] in iterate_distribution_efi(distribution):
        display = distribution.display_name(kernel, preset)
        yield (kernel, preset, base_name, display)
        yield (kernel, preset,
               "{}_backup".format(base_name),
               "{} Backup".format(display))
        yield (kernel, preset,
               "{}_tmpfs".format(base_name),
               "{} tmpfs".format(display))
        yield (kernel, preset,
               "{}_tmpfs_backup".format(base_name),
               "{} tmpfs Backup".format(display))
