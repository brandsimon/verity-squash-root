#!/usr/bin/python3
import argparse
import logging
import os
import sys
from configparser import ConfigParser
from secure_squash_root.config import read_config, LOG_FILE, \
    check_config_and_system, config_str_to_stripped_arr, TMPDIR
from secure_squash_root.decrypt import DecryptKeys
from secure_squash_root.distributions.base import DistributionConfig, \
    calc_kernel_packages_not_unique
from secure_squash_root.distributions.arch import ArchLinuxConfig
from secure_squash_root.file_names import iterate_kernel_variants, \
    kernel_is_ignored
from secure_squash_root.main import create_image_and_sign_kernel
from secure_squash_root.mount import TmpfsMount
from secure_squash_root.setup import add_kernels_to_uefi, setup_systemd_boot


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


def warn_check_system_config(config: ConfigParser,
                             distribution: DistributionConfig) -> bool:
    warnings = check_config_and_system(config) + \
        calc_kernel_packages_not_unique(distribution)
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


def parse_params_and_run():
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
    warned = warn_check_system_config(config, distribution)
    if warned and not args.ignore_warnings:
        logging.error("If you want to ignore those warnings, run with "
                      "--ignore-warnings")
        sys.exit(1)

    if args.command == "list":
        list_distribution_efi(config, distribution)
    elif args.command == "setup":
        with TmpfsMount(TMPDIR):
            with DecryptKeys(config):
                if args.boot_method == "uefi":
                    add_kernels_to_uefi(config, distribution,
                                        args.disk, args.partition_no)
                if args.boot_method == "systemd":
                    setup_systemd_boot(config, distribution)
    elif args.command == "build":
        with TmpfsMount(TMPDIR):
            with DecryptKeys(config):
                create_image_and_sign_kernel(config, distribution)


if __name__ == "__main__":
    parse_params_and_run()
