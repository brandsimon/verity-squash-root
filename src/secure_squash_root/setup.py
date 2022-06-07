import os
from collections.abc import Callable
from configparser import ConfigParser
from secure_squash_root.exec import exec_binary
from secure_squash_root.distributions.base import DistributionConfig, \
    iterate_distribution_efi
from secure_squash_root.config import config_str_to_stripped_arr
import secure_squash_root.efi as efi
from secure_squash_root.file_op import write_str_to


def add_uefi_boot_option(disk: str, partition_no: int, label: str,
                         efi_file: str):
    cmd = ["efibootmgr", "--disk", disk, "--part", str(partition_no),
           "--create", "--label", label, "--loader", efi_file]
    exec_binary(cmd)


def _call_normal_and_backup_with_tmpfs(
        base_name: str, label: str,
        callback: Callable[[str, str], None],
        reverse=False) -> None:
    tasks = []

    def add_normal_and_backup(bn: str, lb: str):
        tasks.append((bn, lb))
        tasks.append(("{}_backup".format(bn), "{} Backup".format(lb)))
        if reverse:
            tasks[-1], tasks[-2] = tasks[-2], tasks[-1]

    add_normal_and_backup(base_name, "{}".format(label))
    add_normal_and_backup("{}_tmpfs".format(base_name),
                          "{} tmpfs".format(label))
    if reverse:
        tasks = list(reversed(tasks))
    for task in tasks:
        callback(task[0], task[1])


def add_kernels_to_uefi(config: ConfigParser, distribution: DistributionConfig,
                        disk: str, partition_no: int) -> None:
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
        display = distribution.display_name(kernel, preset)
        _call_normal_and_backup_with_tmpfs(base_name, display, add,
                                           reverse=True)


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
    ignore_efis = config_str_to_stripped_arr(
        config["DEFAULT"]["IGNORE_KERNEL_EFIS"])

    def add(base_name, label):
        if base_name not in ignore_efis:
            binary = os.path.join(out_dir, "{}.efi".format(base_name))
            out = os.path.join(entries_dir, "{}.conf".format(base_name))
            text = "title {}\nlinux {}\n".format(label, binary)
            write_str_to(out, text)

    kernels = list(iterate_distribution_efi(distribution))
    for [kernel, preset, base_name] in kernels:
        display = distribution.display_name(kernel, preset)
        _call_normal_and_backup_with_tmpfs(base_name, display, add)
