TMPDIR = "/tmp/secure_squash_root"
KERNEL_PARAM_BASE = "secure_squash_root"


def str_to_exclude_dirs(s: str) -> [str]:
    return [i.strip() for i in s.split(",")]
