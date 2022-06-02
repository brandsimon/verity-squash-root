from secure_squash_root.exec import run_prog
from secure_squash_root.config import KERNEL_PARAM_BASE


def file_matches_slot(file: str, slot: str):
    search_str = " {}_slot={} ".format(KERNEL_PARAM_BASE, slot)
    result = run_prog(["objcopy", "--dump-section", ".cmdline=/dev/stdout",
                       file])
    text = result[0].decode()
    return search_str in text
