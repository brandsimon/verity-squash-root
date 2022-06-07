#!/usr/bin/python3
import argparse
import os
import shutil
from configparser import ConfigParser
import secure_squash_root.cmdline as cmdline
import secure_squash_root.efi as efi
from secure_squash_root.config import TMPDIR, KERNEL_PARAM_BASE, \
    config_str_to_stripped_arr, read_config
from secure_squash_root.exec import exec_binary
from secure_squash_root.file_op import read_text_from, write_str_to
from secure_squash_root.image import mksquashfs, veritysetup_image
from secure_squash_root.distributions.base import DistributionConfig, \
    iterate_distribution_efi
from secure_squash_root.distributions.arch import ArchLinuxConfig
from secure_squash_root.setup import add_kernels_to_uefi


def build_and_sign_kernel(config: ConfigParser, vmlinuz: str, initramfs: str,
                          slot: str, root_hash: str,
                          out: str, add_cmdline: str = "") -> None:
    cmdline = "{} {} {p}_slot={} {p}_hash={}".format(
        config["DEFAULT"]["CMDLINE"],
        add_cmdline,
        slot,
        root_hash,
        p=KERNEL_PARAM_BASE)
    cmdline_file = os.path.join(TMPDIR, "cmdline")
    # Store files to sign on trusted tmpfs
    write_str_to(cmdline_file, cmdline)
    tmp_efi_file = os.path.join(TMPDIR, "tmp.efi")
    efi.create_efi_executable(
        config["DEFAULT"]["EFI_STUB"],
        cmdline_file,
        vmlinuz,
        initramfs,
        tmp_efi_file)
    key_dir = config["DEFAULT"]["SECURE_BOOT_KEYS"]
    efi.sign(key_dir, tmp_efi_file, tmp_efi_file)
    if os.path.exists(out):
        if efi.file_matches_slot(out, slot):
            # if backup slot is booted, dont override it
            os.unlink(out)
        else:
            os.rename(out, "{}.bak".format(out))
    shutil.move(tmp_efi_file, out)


class TmpfsMount():
    _directory: str

    def __init__(self, directory: str):
        self._directory = directory

    def __enter__(self):
        tmp_mount = ["mount", "-t", "tmpfs", "-o",
                     "mode=0700,uid=0,gid=0", "tmpfs", self._directory]
        exec_binary(["mkdir", self._directory])
        exec_binary(tmp_mount)

    def __exit__(self, exc_type, exc_value, exc_tb):
        tmp_umount = ["umount", "-f", "-R", self._directory]
        exec_binary(tmp_umount)
        shutil.rmtree(self._directory)


def create_image_and_sign_kernel(config: ConfigParser,
                                 distribution: DistributionConfig):
    kernel_cmdline = read_text_from("/proc/cmdline")
    use_slot = cmdline.unused_slot(kernel_cmdline)
    root_mount = config["DEFAULT"]["ROOT_MOUNT"]
    image = os.path.join(root_mount, "image_{}.squashfs".format(use_slot))
    efi_partition = config["DEFAULT"]["EFI_PARTITION"]
    exclude_dirs = config_str_to_stripped_arr(
        config["DEFAULT"]["EXCLUDE_DIRS"])
    mksquashfs(exclude_dirs, image, root_mount, efi_partition)
    root_hash = veritysetup_image(image)
    efi_dirname = distribution.efi_dirname()
    print(root_hash)
    ignore_efis = config_str_to_stripped_arr(
        config["DEFAULT"]["IGNORE_KERNEL_EFIS"])

    for [kernel, preset, base_name] in iterate_distribution_efi(distribution):
        vmlinuz = distribution.vmlinuz(kernel)
        print(kernel, preset)
        base_name = distribution.file_name(kernel, preset)
        base_name_tmpfs = "{}_tmpfs".format(base_name)
        if base_name in ignore_efis and base_name_tmpfs in ignore_efis:
            continue

        initramfs = distribution.build_initramfs_with_microcode(
            kernel, preset)
        out_dir = os.path.join(efi_partition, "EFI", efi_dirname)
        if base_name not in ignore_efis:
            out = os.path.join(out_dir, "{}.efi".format(base_name))
            build_and_sign_kernel(config, vmlinuz, initramfs, use_slot,
                                  root_hash, out)

        if base_name_tmpfs not in ignore_efis:
            out_tmpfs = os.path.join(out_dir, "{}.efi".format(base_name_tmpfs))
            build_and_sign_kernel(config, vmlinuz, initramfs, use_slot,
                                  root_hash, out_tmpfs,
                                  "{}_volatile".format(KERNEL_PARAM_BASE))


def list_distribution_efi(distribution: DistributionConfig) -> None:
    for [kernel, preset, base_name] in iterate_distribution_efi(distribution):
        print("kernel: {}, preset: {}".format(kernel, preset))
        print(" - {}".format(base_name))
        print(" - {}_tmpfs".format(base_name))


def main():
    config = read_config()
    distribution = ArchLinuxConfig()
    os.umask(0o077)

    parser = argparse.ArgumentParser()
    cmd_parser = parser.add_subparsers(dest="command", required=True)
    cmd_parser.add_parser("list")
    cmd_parser.add_parser("build")
    setup_parser = cmd_parser.add_parser("setup")
    boot_parser = setup_parser.add_subparsers(dest="boot_method",
                                              required=True)
    efi_parser = boot_parser.add_parser("uefi")
    efi_parser.add_argument("disk")
    efi_parser.add_argument("partition_no", type=int)
    args = parser.parse_args()

    if args.command == "list":
        list_distribution_efi(distribution)
    elif args.command == "setup":
        if args.boot_method == "uefi":
            add_kernels_to_uefi(config, distribution,
                                args.disk, args.partition_no)
    elif args.command == "build":
        with TmpfsMount(TMPDIR):
            create_image_and_sign_kernel(config, distribution)


if __name__ == "__main__":
    main()
