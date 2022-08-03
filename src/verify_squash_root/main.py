import logging
import os
import shutil
from configparser import ConfigParser
from typing import List, Union
import verify_squash_root.cmdline as cmdline
import verify_squash_root.efi as efi
from verify_squash_root.config import TMPDIR, KERNEL_PARAM_BASE, \
    config_str_to_stripped_arr
from verify_squash_root.distributions.base import DistributionConfig, \
    iterate_distribution_efi
from verify_squash_root.file_names import backup_file, tmpfs_file, tmpfs_label
from verify_squash_root.file_op import read_text_from
from verify_squash_root.image import mksquashfs, veritysetup_image


def move_kernel_to(src: str, dst: str, slot: str,
                   dst_backup: Union[str, None]) -> None:
    if os.path.exists(dst):
        overwrite_file = efi.file_matches_slot_or_is_broken(dst, slot)
        if overwrite_file or dst_backup is None:
            # if backup slot is booted, dont override it
            if dst_backup is None:
                logging.debug("Backup ignored")
            elif overwrite_file:
                logging.debug("Backup slot kept as is")
            os.unlink(dst)
        else:
            logging.info("Moving old efi to backup")
            logging.debug("Path: {}".format(dst_backup))
            os.rename(dst, dst_backup)
    shutil.move(src, dst)


def create_squashfs_return_verity_hash(config: ConfigParser, use_slot: str) \
        -> str:
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
    return root_hash


def build_and_move_kernel(config: ConfigParser,
                          vmlinuz: str, initramfs: str,
                          use_slot: str, root_hash: str, cmdline_add: str,
                          base_name: str, out_dir: str,
                          label: str,
                          ignore_efis: List[str]):
    if base_name in ignore_efis:
        return
    logging.info("Processing {}".format(label))
    out = os.path.join(out_dir, "{}.efi".format(base_name))
    backup_out = None
    backup_base_name = backup_file(base_name)
    if backup_base_name not in ignore_efis:
        backup_out = os.path.join(
            out_dir, "{}.efi".format(backup_base_name))
    logging.debug("Write efi to {}".format(out))
    # Store files to sign on trusted tmpfs
    tmp_efi_file = os.path.join(TMPDIR, "tmp.efi")
    efi.build_and_sign_kernel(config, vmlinuz, initramfs, use_slot,
                              root_hash, tmp_efi_file,
                              cmdline_add)
    move_kernel_to(tmp_efi_file, out, use_slot, backup_out)


def create_image_and_sign_kernel(config: ConfigParser,
                                 distribution: DistributionConfig):
    kernel_cmdline = read_text_from("/proc/cmdline")
    use_slot = cmdline.unused_slot(kernel_cmdline)
    efi_partition = config["DEFAULT"]["EFI_PARTITION"]
    efi_dirname = distribution.efi_dirname()
    out_dir = os.path.join(efi_partition, "EFI", efi_dirname)
    logging.info("Using slot {} for new image".format(use_slot))
    root_hash = create_squashfs_return_verity_hash(config, use_slot)
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
            build_and_move_kernel(config, vmlinuz, initramfs,
                                  use_slot, root_hash, cmdline_add,
                                  bn, out_dir, label,
                                  ignore_efis)

        build(base_name, display, "")
        build(base_name_tmpfs, tmpfs_label(display),
              "{}_volatile".format(KERNEL_PARAM_BASE))
