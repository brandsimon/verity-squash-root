#!/usr/bin/python3
import argparse
import logging
import os
import shutil
import sys
from configparser import ConfigParser
from typing import Union
import secure_squash_root.cmdline as cmdline
import secure_squash_root.efi as efi
from secure_squash_root.config import TMPDIR, KERNEL_PARAM_BASE, \
    config_str_to_stripped_arr, read_config, LOG_FILE, check_config_and_system
from secure_squash_root.file_op import read_text_from, write_str_to
from secure_squash_root.image import mksquashfs, veritysetup_image
from secure_squash_root.distributions.base import DistributionConfig, \
    iterate_distribution_efi
from secure_squash_root.distributions.arch import ArchLinuxConfig
from secure_squash_root.setup import add_kernels_to_uefi, setup_systemd_boot
from secure_squash_root.file_names import iterate_kernel_variants, \
    backup_file, tmpfs_file, kernel_is_ignored, tmpfs_label
from secure_squash_root.mount import TmpfsMount


def build_and_sign_kernel(config: ConfigParser, vmlinuz: str, initramfs: str,
                          slot: str, root_hash: str,
                          tmp_efi_file: str, add_cmdline: str = "") -> None:
    cmdline = "{} {} {p}_slot={} {p}_hash={}".format(
        config["DEFAULT"]["CMDLINE"],
        add_cmdline,
        slot,
        root_hash,
        p=KERNEL_PARAM_BASE)
    cmdline_file = os.path.join(TMPDIR, "cmdline")
    # Store files to sign on trusted tmpfs
    write_str_to(cmdline_file, cmdline)
    efi.create_efi_executable(
        config["DEFAULT"]["EFI_STUB"],
        cmdline_file,
        vmlinuz,
        initramfs,
        tmp_efi_file)
    key_dir = config["DEFAULT"]["SECURE_BOOT_KEYS"]
    efi.sign(key_dir, tmp_efi_file, tmp_efi_file)


def move_kernel_to(src: str, dst: str, slot: str,
                   dst_backup: Union[str, None]) -> None:
    if os.path.exists(dst):
        slot_matches = efi.file_matches_slot(dst, slot)
        if slot_matches or dst_backup is None:
            # if backup slot is booted, dont override it
            if dst_backup is None:
                logging.debug("Backup ignored")
            elif slot_matches:
                logging.debug("Backup slot kept as is")
            os.unlink(dst)
        else:
            logging.info("Moving old efi to backup")
            logging.debug("Path: {}".format(dst_backup))
            os.rename(dst, dst_backup)
    shutil.move(src, dst)


def create_image_and_sign_kernel(config: ConfigParser,
                                 distribution: DistributionConfig):
    kernel_cmdline = read_text_from("/proc/cmdline")
    use_slot = cmdline.unused_slot(kernel_cmdline)
    logging.info("Using slot {} for new image".format(use_slot))
    root_mount = config["DEFAULT"]["ROOT_MOUNT"]
    image = os.path.join(root_mount, "image_{}.squashfs".format(use_slot))
    logging.debug("Image path: {}".format(image))
    efi_partition = config["DEFAULT"]["EFI_PARTITION"]
    exclude_dirs = config_str_to_stripped_arr(
        config["DEFAULT"]["EXCLUDE_DIRS"])
    logging.info("Creating squashfs...")
    mksquashfs(exclude_dirs, image, root_mount, efi_partition)
    logging.info("Setup device verity")
    root_hash = veritysetup_image(image)
    efi_dirname = distribution.efi_dirname()
    out_dir = os.path.join(efi_partition, "EFI", efi_dirname)
    logging.debug("Calculated root hash: {}".format(root_hash))
    ignore_efis = config_str_to_stripped_arr(
        config["DEFAULT"]["IGNORE_KERNEL_EFIS"])

    for [kernel, preset, base_name] in iterate_distribution_efi(distribution):
        vmlinuz = distribution.vmlinuz(kernel)
        base_name = distribution.file_name(kernel, preset)
        base_name_tmpfs = tmpfs_file(base_name)
        display = distribution.display_name(kernel, preset)

        if base_name in ignore_efis and base_name_tmpfs in ignore_efis:
            logging.info("skipping due to ignored kernels")
            continue

        logging.info("Create initramfs for {}".format(display))
        initramfs = distribution.build_initramfs_with_microcode(
            kernel, preset)

        def build(bn, label, cmdline_add):
            if bn not in ignore_efis:
                logging.info("Processing {}".format(label))
                out = os.path.join(out_dir, "{}.efi".format(bn))
                logging.debug("Write efi to {}".format(out))
                backup_out = None
                backup_bn = backup_file(bn)
                if backup_bn not in ignore_efis:
                    backup_out = os.path.join(
                        out_dir, "{}.efi".format(backup_bn))
                tmp_efi_file = os.path.join(TMPDIR, "tmp.efi")
                build_and_sign_kernel(config, vmlinuz, initramfs, use_slot,
                                      root_hash, tmp_efi_file,
                                      cmdline_add)
                move_kernel_to(tmp_efi_file, out, use_slot, backup_out)

        build(base_name, display, "")
        build(base_name_tmpfs, tmpfs_label(display),
              "{}_volatile".format(KERNEL_PARAM_BASE))


def list_distribution_efi(config: ConfigParser,
                          distribution: DistributionConfig) -> None:
    ignore_efis = config_str_to_stripped_arr(
        config["DEFAULT"]["IGNORE_KERNEL_EFIS"])
    last = ("", "")

    for (kernel, preset, base_name, display) in iterate_kernel_variants(
            distribution):
        ident = (kernel, preset)
        if ident != last:
            print("{}: kernel: {}, preset: {}".format(display, kernel, preset))
        last = ident

        op = "-" if kernel_is_ignored(base_name, ignore_efis) else "+"
        print(" {} {} ({})".format(op, base_name, display))
    print("\n(+ = included, - = excluded")


def warn_check_system_config(config: ConfigParser) -> bool:
    warnings = check_config_and_system(config)
    for line in warnings:
        logging.warning(line)
    return len(warnings) > 0


def configure_logger(verbose: bool) -> None:
    loglevel = logging.INFO if not verbose else logging.DEBUG
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        encoding="utf-8",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger()
    logger.handlers[0].setLevel(logging.DEBUG)
    logger.handlers[1].setLevel(loglevel)


def main():
    os.umask(0o077)
    config = read_config()
    distribution = ArchLinuxConfig()

    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--ignore-warnings", action="store_true")
    cmd_parser = parser.add_subparsers(dest="command", required=True)
    cmd_parser.add_parser("list")
    cmd_parser.add_parser("check")
    cmd_parser.add_parser("build")
    setup_parser = cmd_parser.add_parser("setup")
    boot_parser = setup_parser.add_subparsers(dest="boot_method",
                                              required=True)
    boot_parser.add_parser("systemd")
    efi_parser = boot_parser.add_parser("uefi")
    efi_parser.add_argument("disk")
    efi_parser.add_argument("partition_no", type=int)
    args = parser.parse_args()
    configure_logger(args.verbose)

    logging.debug("Running: {}".format(sys.argv))
    logging.debug("Parsed arguments: {}".format(args))
    warned = warn_check_system_config(config)
    if warned and not args.ignore_warnings:
        logging.error("If you want to ignore those warnings, run with "
                      "--ignore-warnings")
        sys.exit(1)

    if args.command == "list":
        list_distribution_efi(config, distribution)
    elif args.command == "setup":
        if args.boot_method == "uefi":
            add_kernels_to_uefi(config, distribution,
                                args.disk, args.partition_no)
        if args.boot_method == "systemd":
            setup_systemd_boot(config, distribution)
    elif args.command == "build":
        with TmpfsMount(TMPDIR):
            create_image_and_sign_kernel(config, distribution)


if __name__ == "__main__":
    main()
