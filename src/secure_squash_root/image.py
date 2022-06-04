import secure_squash_root.parsing as parsing
from secure_squash_root.exec import exec_binary


def mksquashfs(exclude_dirs: [str], image: str,
               root_mount: str, efi_partition) -> str:
    include_dirs = ["/"]
    include_empty_dirs = ["dev", "proc", "run", "sys", "tmp", root_mount,
                          efi_partition] + exclude_dirs
    options = ["-reproducible", "-xattrs", "-wildcards", "-noappend",
               "-p", "{} d 0700 0 0".format(root_mount),
               "-p", "{} d 0700 0 0".format(efi_partition)]
    cmd = ["mksquashfs"] + include_dirs + [image] + options + ["-e"]
    for d in include_empty_dirs:
        sd = d.strip("/")
        cmd += ["{}/*".format(sd)]
        cmd += ["{}/.*".format(sd)]
    exec_binary(cmd)


def veritysetup_image(image: str) -> str:
    cmd = ["veritysetup", "format", image, "{}.verity".format(image)]
    result = exec_binary(cmd)
    stdout = result[0].decode()
    info = parsing.info_to_dict(stdout)
    return info["Root hash"]
