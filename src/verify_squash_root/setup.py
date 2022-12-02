from configparser import ConfigParser
from pathlib import Path
from verity_squash_root.distributions.base import DistributionConfig, \
    InitramfsBuilder
from verity_squash_root.exec import exec_binary
from verity_squash_root.config import KEY_DIR
import verity_squash_root.efi as efi
from verity_squash_root.file_op import write_str_to
from verity_squash_root.file_names import iterate_non_ignored_kernel_variants

EFI_PATH = Path("/EFI")


def add_uefi_boot_option(disk: str, partition_no: int, label: str,
                         efi_file: Path):
    cmd = ["efibootmgr", "--disk", disk, "--part", str(partition_no),
           "--create", "--label", label, "--loader", str(efi_file)]
    exec_binary(cmd)


def add_kernels_to_uefi(config: ConfigParser, distribution: DistributionConfig,
                        initramfs: InitramfsBuilder,
                        disk: str, partition_no: int) -> None:
    efi_dirname = distribution.efi_dirname()
    out_dir = EFI_PATH / efi_dirname

    # Use reversed order, because last added option is sometimes
    # the default boot option
    kernels = reversed(list(iterate_non_ignored_kernel_variants(
        config, distribution, initramfs)))
    for (kernel, preset, base_name, label) in kernels:
        out = out_dir / "{}.efi".format(base_name)
        add_uefi_boot_option(disk, partition_no, label, out)


def setup_systemd_boot(config: ConfigParser,
                       distribution: DistributionConfig,
                       initramfs: InitramfsBuilder) -> None:
    exec_binary(["bootctl", "install"])
    boot_efi = Path("/usr/lib/systemd/boot/efi/systemd-bootx64.efi")
    efi.sign(KEY_DIR, boot_efi,
             Path("/boot/efi/EFI/systemd/systemd-bootx64.efi"))
    efi.sign(KEY_DIR, boot_efi, Path("/boot/efi/EFI/BOOT/BOOTX64.EFI"))

    efi_dirname = distribution.efi_dirname()
    out_dir = EFI_PATH / efi_dirname
    entries_dir = Path(config["DEFAULT"]["EFI_PARTITION"]) / "loader/entries"

    for (kernel, preset, base_name, label) in \
            iterate_non_ignored_kernel_variants(config, distribution,
                                                initramfs):
        binary = out_dir / "{}.efi".format(base_name)
        out = entries_dir / "{}.conf".format(base_name)
        text = "title {}\nlinux {}\n".format(label, binary)
        write_str_to(out, text)
