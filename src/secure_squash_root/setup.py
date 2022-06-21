import os
from configparser import ConfigParser
from verify_squash_root.exec import exec_binary
from verify_squash_root.distributions.base import DistributionConfig
import verify_squash_root.efi as efi
from verify_squash_root.file_op import write_str_to
from verify_squash_root.file_names import iterate_non_ignored_kernel_variants


def add_uefi_boot_option(disk: str, partition_no: int, label: str,
                         efi_file: str):
    cmd = ["efibootmgr", "--disk", disk, "--part", str(partition_no),
           "--create", "--label", label, "--loader", efi_file]
    exec_binary(cmd)


def add_kernels_to_uefi(config: ConfigParser, distribution: DistributionConfig,
                        disk: str, partition_no: int) -> None:
    efi_dirname = distribution.efi_dirname()
    out_dir = os.path.join("/EFI", efi_dirname)

    # Use reversed order, because last added option is sometimes
    # the default boot option
    kernels = reversed(list(iterate_non_ignored_kernel_variants(
        config, distribution)))
    for (kernel, preset, base_name, label) in kernels:
        out = os.path.join(out_dir, "{}.efi".format(base_name))
        add_uefi_boot_option(disk, partition_no, label, out)


def setup_systemd_boot(config: ConfigParser,
                       distribution: DistributionConfig) -> None:
    key_dir = config["DEFAULT"]["SECURE_BOOT_KEYS"]
    exec_binary(["bootctl", "install"])
    boot_efi = "/usr/lib/systemd/boot/efi/systemd-bootx64.efi"
    efi.sign(key_dir, boot_efi, "/boot/efi/EFI/systemd/systemd-bootx64.efi")
    efi.sign(key_dir, boot_efi, "/boot/efi/EFI/BOOT/BOOTX64.EFI")

    efi_dirname = distribution.efi_dirname()
    out_dir = os.path.join("/EFI", efi_dirname)
    entries_dir = os.path.join(config["DEFAULT"]["EFI_PARTITION"],
                               "loader/entries")

    for (kernel, preset, base_name, label) in \
            iterate_non_ignored_kernel_variants(config, distribution):
        binary = os.path.join(out_dir, "{}.efi".format(base_name))
        out = os.path.join(entries_dir, "{}.conf".format(base_name))
        text = "title {}\nlinux {}\n".format(label, binary)
        write_str_to(out, text)
