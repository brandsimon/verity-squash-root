#!/usr/bin/python3
import argparse
import logging
import os
import shutil
import sys
import verity_squash_root.encrypt as encrypt
from configparser import ConfigParser
from verity_squash_root.config import read_config, LOG_FILE, \
    check_config_and_system, config_str_to_stripped_arr, TMPDIR, CONFIG_FILE
from verity_squash_root.decrypt import DecryptKeys
from verity_squash_root.distributions.base import DistributionConfig, \
    calc_kernel_packages_not_unique
from verity_squash_root.distributions.arch import ArchLinuxConfig
from verity_squash_root.initramfs.mkinitcpio import InitramfsBuilder, \
    Mkinitcpio
from verity_squash_root.file_names import iterate_kernel_variants, \
    kernel_is_ignored
from verity_squash_root.main import create_image_and_sign_kernel, \
    backup_and_sign_extra_files
from verity_squash_root.mount import TmpfsMount
from verity_squash_root.setup import add_kernels_to_uefi, setup_systemd_boot


def list_distribution_efi(config: ConfigParser,
                          distribution: DistributionConfig,
                          initramfs: InitramfsBuilder) -> None:
    ignore_efis = config_str_to_stripped_arr(
        config["DEFAULT"]["IGNORE_KERNEL_EFIS"])
    last = ("", "")

    for (kernel, preset, base_name, display) in iterate_kernel_variants(
            distribution, initramfs):
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
    initramfs = Mkinitcpio(distribution)

    parser = argparse.ArgumentParser(
        description="Create signed efi binaries which mount a verified "
                    "squashfs (dm-verity) image\nas rootfs on boot "
                    "(in the initramfs/initrd). "
                    "On boot you can choose to boot\ninto a tmpfs overlay or "
                    "a directory (/overlay and /workdir) on your\n"
                    "root-partition.\n\n"
                    "The configuration file is located at {}".format(
                        CONFIG_FILE),
                    formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--verbose",
                        action="store_true",
                        help="Show debug messages on the terminal")
    parser.add_argument("--ignore-warnings",
                        action="store_true",
                        help="Do not exit if there are warnings")
    cmd_parser = parser.add_subparsers(dest="command", required=True)
    cmd_parser.add_parser("create-keys",
                          help="Create secure boot keys and store them "
                               "(age needs to be installed)")
    cmd_parser.add_parser("list",
                          help="List all efi files to build and show "
                               "which ones are\nbuilt and which ones "
                               "are excluded via configfile.")
    cmd_parser.add_parser("check",
                          help="Check the system and print warnings if "
                               "the\nconfiguration does not match the "
                               "recommendation.")
    cmd_parser.add_parser("build",
                          help="Build squashfs, verity-info, efi binaries "
                               "and sign\nthem.")
    setup_parser = cmd_parser.add_parser("setup",
                                         formatter_class=(
                                             argparse.RawTextHelpFormatter),
                                         help="Setup boot menu entries for "
                                              "all efi binaries which are"
                                              "\nnot excluded. Supported: \n"
                                              " - systemd: systemd-boot\n"
                                              " - uefi: efibootmgr")
    boot_parser = setup_parser.add_subparsers(dest="boot_method",
                                              required=True)
    boot_parser.add_parser("systemd",
                           help="Install and configure systemd-boot and "
                                "register it in the\nuefi as bootable.")
    efi_parser = boot_parser.add_parser("uefi",
                                        help="Register all efi binaries in "
                                             "the uefi as bootable via\n"
                                             "efibootmgr.")
    efi_parser.add_argument("disk",
                            help="Parameter for efibootmgr --disk")
    efi_parser.add_argument("partition_no",
                            help="Parameter for efibootmgr --part",
                            type=int)
    cmd_parser.add_parser("sign-extra-files",
                          help="Sign all files specified in the EXTRA_SIGN "
                               "section in the config file.")
    args = parser.parse_args()
    configure_logger(args.verbose)

    logging.debug("Running: {}".format(sys.argv))
    logging.debug("Parsed arguments: {}".format(args))
    warned = warn_check_system_config(config, distribution)
    if warned and not args.ignore_warnings:
        logging.error("If you want to ignore those warnings, run with "
                      "--ignore-warnings")
        sys.exit(1)

    try:
        if args.command == "create-keys":
            if shutil.which("age") is None:
                raise FileNotFoundError("age is not installed, but needed "
                                        "for encryption")
            with TmpfsMount(TMPDIR):
                encrypt.check_if_archives_exist()
                encrypt.create_and_pack_secure_boot_keys()
        elif args.command == "list":
            list_distribution_efi(config, distribution, initramfs)
        elif args.command == "setup":
            with TmpfsMount(TMPDIR):
                if args.boot_method == "uefi":
                    add_kernels_to_uefi(config, distribution, initramfs,
                                        args.disk, args.partition_no)
                if args.boot_method == "systemd":
                    with DecryptKeys(config):
                        setup_systemd_boot(config, distribution, initramfs)
        elif args.command == "build":
            with TmpfsMount(TMPDIR):
                with DecryptKeys(config):
                    create_image_and_sign_kernel(config, distribution,
                                                 initramfs)
        elif args.command == "sign-extra-files":
            with TmpfsMount(TMPDIR):
                with DecryptKeys(config):
                    backup_and_sign_extra_files(config)
    except BaseException as e:
        logging.error("Error: {}".format(e))
        logging.debug(e, exc_info=1)
        logging.error("For more info use the --verbose option "
                      "or look into the log file: {}".format(LOG_FILE))


if __name__ == "__main__":
    parse_params_and_run()
