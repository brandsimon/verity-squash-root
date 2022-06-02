import os
from secure_squash_root.exec import exec_binary
from secure_squash_root.config import KERNEL_PARAM_BASE


def file_matches_slot(file: str, slot: str):
    search_str = " {}_slot={} ".format(KERNEL_PARAM_BASE, slot)
    result = exec_binary(["objcopy", "--dump-section", ".cmdline=/dev/stdout",
                          file])
    text = result[0].decode()
    return search_str in text


def sign(key_dir: str, in_file: str, out_file: str) -> None:
    exec_binary([
        "sbsign",
        "--key", os.path.join(key_dir, "db.key"),
        "--cert",  os.path.join(key_dir, "db.crt"),
        "--output", out_file, in_file])
