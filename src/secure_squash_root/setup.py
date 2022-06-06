import os
from configparser import ConfigParser
from secure_squash_root.exec import exec_binary
from secure_squash_root.distributions.base import DistributionConfig, \
    iterate_distribution_efi
from secure_squash_root.config import config_str_to_stripped_arr


def add_uefi_boot_option(disk: str, partition_no: int, label: str,
                         efi_file: str):
    cmd = ["efibootmgr", "--disk", disk, "--part", str(partition_no),
           "--create", "--label", label, "--loader", efi_file]
    exec_binary(cmd)


def add_kernels_to_uefi(config: ConfigParser, distribution: DistributionConfig,
                        disk: str, partition_no: int,) -> None:
    efi_dirname = distribution.efi_dirname()
    out_dir = os.path.join("/EFI", efi_dirname)
    ignore_efis = config_str_to_stripped_arr(
        config["DEFAULT"]["IGNORE_KERNEL_EFIS"])

    def add(base_name, label):
        if base_name not in ignore_efis:
            out = os.path.join(out_dir, "{}.efi".format(base_name))
            add_uefi_boot_option(disk, partition_no, label, out)

    kernels = reversed(list(iterate_distribution_efi(distribution)))
    for [kernel, preset, base_name] in kernels:
        add("{}_tmpfs".format(base_name),
            "{} {} tmpfs".format(efi_dirname, base_name))
        add(base_name, "{} {}".format(efi_dirname, base_name))
