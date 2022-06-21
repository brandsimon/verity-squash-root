import os
from configparser import ConfigParser
from verify_squash_root.config import KERNEL_PARAM_BASE, TMPDIR, KEY_DIR
from verify_squash_root.exec import exec_binary
from verify_squash_root.file_op import write_str_to


def file_matches_slot(file: str, slot: str):
    search_str = " {}_slot={} ".format(KERNEL_PARAM_BASE, slot)
    result = exec_binary(["objcopy", "-O", "binary", "--only-section",
                          ".cmdline", file, "/dev/stdout"])
    text = result[0].decode()
    return search_str in text


def sign(key_dir: str, in_file: str, out_file: str) -> None:
    exec_binary([
        "sbsign",
        "--key", os.path.join(key_dir, "db.key"),
        "--cert",  os.path.join(key_dir, "db.crt"),
        "--output", out_file, in_file])


def create_efi_executable(stub: str, cmdline_file: str, linux: str,
                          initrd: str, dest: str):
    exec_binary([
        "objcopy",
        "--add-section", ".osrel=/etc/os-release",
        "--change-section-vma", ".osrel=0x20000",
        "--add-section", ".cmdline={}".format(cmdline_file),
        "--change-section-vma", ".cmdline=0x30000",
        "--add-section", ".linux={}".format(linux),
        "--change-section-vma", ".linux=0x2000000",
        "--add-section", ".initrd={}".format(initrd),
        "--change-section-vma", ".initrd=0x3000000",
        stub, dest])


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
    write_str_to(cmdline_file, cmdline)
    create_efi_executable(
        config["DEFAULT"]["EFI_STUB"],
        cmdline_file,
        vmlinuz,
        initramfs,
        tmp_efi_file)
    sign(KEY_DIR, tmp_efi_file, tmp_efi_file)
