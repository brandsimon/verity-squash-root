import os
from tempfile import NamedTemporaryFile
from secure_squash_root.exec import exec_binary
from secure_squash_root.config import KERNEL_PARAM_BASE


def file_matches_slot(file: str, slot: str):
    search_str = " {}_slot={} ".format(KERNEL_PARAM_BASE, slot)
    # objcopy will modify the file, so use an output file
    with NamedTemporaryFile() as tmpfile:
        result = exec_binary(["objcopy", "--dump-section",
                              ".cmdline=/dev/stdout", file, tmpfile.name])
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
