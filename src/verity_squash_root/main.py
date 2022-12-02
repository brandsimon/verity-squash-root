import logging
import shutil
from pathlib import Path
from configparser import ConfigParser
from typing import List, Union
import verity_squash_root.cmdline as cmdline
import verity_squash_root.efi as efi
from verity_squash_root.config import TMPDIR, KERNEL_PARAM_BASE, KEY_DIR, \
    config_str_to_stripped_arr
from verity_squash_root.distributions.base import DistributionConfig, \
    InitramfsBuilder, iterate_distribution_efi
from verity_squash_root.file_names import backup_file, tmpfs_file, tmpfs_label
from verity_squash_root.file_op import read_text_from
from verity_squash_root.image import mksquashfs, veritysetup_image


def move_kernel_to(src: Path, dst: Path, slot: str,
                   dst_backup: Union[Path, None]) -> None:
    if dst.exists():
        overwrite_file = efi.file_matches_slot_or_is_broken(dst, slot)
        if overwrite_file or dst_backup is None:
            # if backup slot is booted, dont override it
            if dst_backup is None:
                logging.debug("Backup ignored")
            elif overwrite_file:
                logging.debug("Backup slot kept as is")
            dst.unlink()
        else:
            logging.info("Moving old efi to backup")
            logging.debug("Path: {}".format(dst_backup))
            dst.replace(dst_backup)
    shutil.move(src, dst)


def create_squashfs_return_verity_hash(config: ConfigParser, use_slot: str) \
        -> str:
    root_mount = Path(config["DEFAULT"]["ROOT_MOUNT"])
    image = root_mount / "image_{}.squashfs".format(use_slot)
    logging.debug("Image path: {}".format(image))
    efi_partition = Path(config["DEFAULT"]["EFI_PARTITION"])
    exclude_dirs = config_str_to_stripped_arr(
        config["DEFAULT"]["EXCLUDE_DIRS"])
    logging.info("Creating squashfs...")
    mksquashfs(exclude_dirs, image, root_mount, efi_partition)
    logging.info("Setup device verity")
    root_hash = veritysetup_image(image)
    return root_hash


def build_and_move_kernel(config: ConfigParser,
                          vmlinuz: Path, initramfs: Path,
                          use_slot: str, root_hash: str, cmdline_add: str,
                          base_name: str, out_dir: Path,
                          label: str,
                          ignore_efis: List[str]):
    if base_name in ignore_efis:
        return
    logging.info("Processing {}".format(label))
    out = out_dir / "{}.efi".format(base_name)
    backup_out = None
    backup_base_name = backup_file(base_name)
    if backup_base_name not in ignore_efis:
        backup_out = out_dir / "{}.efi".format(backup_base_name)
    logging.debug("Write efi to {}".format(out))
    # Store files to sign on trusted tmpfs
    tmp_efi_file = TMPDIR / "tmp.efi"
    efi.build_and_sign_kernel(config, vmlinuz, initramfs, use_slot,
                              root_hash, tmp_efi_file,
                              cmdline_add)
    move_kernel_to(tmp_efi_file, out, use_slot, backup_out)


def create_image_and_sign_kernel(config: ConfigParser,
                                 distribution: DistributionConfig,
                                 initramfs: InitramfsBuilder):
    kernel_cmdline = read_text_from(Path("/proc/cmdline"))
    use_slot = cmdline.unused_slot(kernel_cmdline)
    efi_partition = Path(config["DEFAULT"]["EFI_PARTITION"])
    efi_dirname = distribution.efi_dirname()
    out_dir = efi_partition / "EFI" / efi_dirname
    logging.info("Using slot {} for new image".format(use_slot))
    root_hash = create_squashfs_return_verity_hash(config, use_slot)
    logging.debug("Calculated root hash: {}".format(root_hash))
    ignore_efis = config_str_to_stripped_arr(
        config["DEFAULT"]["IGNORE_KERNEL_EFIS"])

    for [kernel, preset, base_name] in iterate_distribution_efi(distribution,
                                                                initramfs):
        vmlinuz = distribution.vmlinuz(kernel)
        base_name = initramfs.file_name(kernel, preset)
        base_name_tmpfs = tmpfs_file(base_name)
        display = initramfs.display_name(kernel, preset)

        if base_name in ignore_efis and base_name_tmpfs in ignore_efis:
            logging.info("skipping due to ignored kernels")
            continue

        logging.info("Create initramfs for {}".format(display))
        initramfs_path = initramfs.build_initramfs_with_microcode(
            kernel, preset)

        def build(bn, label, cmdline_add):
            build_and_move_kernel(config, vmlinuz, initramfs_path,
                                  use_slot, root_hash, cmdline_add,
                                  bn, out_dir, label,
                                  ignore_efis)

        build(base_name, display, "")
        build(base_name_tmpfs, tmpfs_label(display),
              "{}_volatile".format(KERNEL_PARAM_BASE))


def backup_and_sign_efi(source: Path, dest: Path):
    if dest.exists():
        parent = dest.parent
        backup_name = backup_file(dest.stem) + "." + dest.suffix
        backup = parent / backup_name
        dest.replace(backup)
    efi.sign(KEY_DIR, source, dest)


def backup_and_sign_extra_files(config: ConfigParser):
    extra = config["EXTRA_SIGN"]
    for key in extra.keys():
        logging.info("Signing {}...".format(key))
        files = extra[key].split("=>")
        if len(files) != 2:
            raise ValueError("extra signing files need to be specified as\n"
                             "name = SOURCE => DEST")
        src = files[0].strip()
        dest = files[1].strip()
        logging.debug("Sign file '{}' to '{}'".format(src, dest))
        backup_and_sign_efi(Path(src), Path(dest))
