from secure_squash_root.config import KERNEL_PARAM_BASE


def current_slot(kernel_cmdline: str) -> str:
    params = kernel_cmdline.split(" ")
    for p in params:
        if p.startswith("{}_slot=".format(KERNEL_PARAM_BASE)):
            return p[24:].lower()
    return None


def unused_slot(kernel_cmdline: str) -> str:
    curr = current_slot(kernel_cmdline)
    try:
        next_slot = {"a": "b", "b": "a"}
        return next_slot[curr]
    except KeyError:
        return "a"
