from pathlib import Path
from typing import List
import verity_squash_root.parsing as parsing
from verity_squash_root.exec import exec_binary


def mksquashfs(exclude_dirs: List[str], image: Path,
               root_mount: Path, efi_partition: Path):
    include_dirs = ["/"]
    include_empty_dirs = ["dev", "proc", "run", "sys", "tmp", str(root_mount),
                          str(efi_partition)] + exclude_dirs
    options = ["-reproducible", "-xattrs", "-wildcards", "-noappend",
               # prevents overlayfs corruption on updates
               "-no-exports",
               "-p", "{} d 0700 0 0".format(root_mount),
               "-p", "{} d 0700 0 0".format(efi_partition)]
    cmd = ["mksquashfs"] + include_dirs + [str(image)] + options + ["-e"]
    for d in include_empty_dirs:
        sd = d.strip("/")
        cmd += ["{}/*".format(sd)]
        cmd += ["{}/.*".format(sd)]
    exec_binary(cmd)


def verity_image_path(image: Path) -> Path:
    return image.with_suffix("{}.verity".format(image.suffix))


def veritysetup_image(image: Path) -> str:
    cmd = ["veritysetup", "format", str(image), str(verity_image_path(image))]
    result = exec_binary(cmd)
    stdout = result[0].decode()
    info = parsing.info_to_dict(stdout)
    return info["Root hash"]
