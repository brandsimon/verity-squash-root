import logging
from collections import OrderedDict
from configparser import ConfigParser
from pathlib import Path
from verity_squash_root.config import KERNEL_PARAM_BASE, TMPDIR, KEY_DIR
from verity_squash_root.exec import exec_binary, ExecBinaryError
from verity_squash_root.file_op import write_str_to

DB_CERT_FILE = "db.crt"
DB_KEY_FILE = "db.key"
CMDLINE_FILE = Path("/etc/kernel/cmdline")


def file_matches_slot_or_is_broken(file: Path, slot: str):
    search_str = " {}_slot={} ".format(KERNEL_PARAM_BASE, slot)
    try:
        result = exec_binary(["objcopy", "-O", "binary", "--only-section",
                              ".cmdline", str(file), "/dev/fd/1"])
    except ExecBinaryError as e:
        err = e.stderr()
        if err.startswith("objcopy:") and err.endswith(": file truncated\n"):
            logging.warning("Old efi file was truncated")
            logging.debug(err)
            return True
        if err.startswith("objcopy: error: the input file '") and (
                err.endswith("' is empty\n")):
            logging.warning("Old efi file was empty")
            logging.debug(err)
            return True
        raise e
    text = result[0].decode()
    return search_str in text


def sign(key_dir: Path, in_file: Path, out_file: Path) -> None:
    exec_binary([
        "sbsign",
        "--key", str(key_dir / DB_KEY_FILE),
        "--cert",  str(key_dir / DB_CERT_FILE),
        "--output", str(out_file), str(in_file)])


def calculate_efi_stub_end(stub: Path) -> int:
    result = exec_binary(["objdump", "-h", str(stub)])
    lines = result[0].decode().split("\n")
    words = lines[-3].split()
    return int(words[2], 16) + int(words[3], 16)


def create_efi_executable(stub: Path, cmdline_file: Path, linux: Path,
                          initrd: Path, dest: Path):
    offset = calculate_efi_stub_end(stub)
    sections = OrderedDict()
    sections["osrel"] = Path("/etc/os-release")
    sections["cmdline"] = cmdline_file
    sections["initrd"] = initrd
    # place linux at the end so decompressing it in-place does not
    # cause problems:
    # https://github.com/systemd/systemd/commit/
    # 0fa2cac4f0cdefaf1addd7f1fe0fd8113db9360b#commitcomment-84868898
    sections["linux"] = linux

    cmd = ["objcopy"]
    for name, file in sections.items():
        size = file.stat().st_size
        cmd += ["--add-section", ".{}={}".format(name, str(file)),
                "--change-section-vma", ".{}={}".format(name, hex(offset))]
        offset = offset + size
    cmd += [str(stub), str(dest)]
    exec_binary(cmd)


def get_cmdline(config: ConfigParser) -> str:
    con_line = config["DEFAULT"].get("CMDLINE")
    if con_line is not None:
        return con_line
    if CMDLINE_FILE.exists():
        return CMDLINE_FILE.read_text().replace("\n", " ")
    raise RuntimeError("CMDLINE not configured, either configure it in the "
                       "config file or in {}".format(CMDLINE_FILE))


def build_and_sign_kernel(config: ConfigParser, vmlinuz: Path, initramfs: Path,
                          slot: str, root_hash: str,
                          tmp_efi_file: Path, add_cmdline: str = "") -> None:
    # add rw, if root is mounted ro, it cannot be mounted rw later
    cmdline = "{} rw {} {p}_slot={} {p}_hash={}".format(
        get_cmdline(config),
        add_cmdline,
        slot,
        root_hash,
        p=KERNEL_PARAM_BASE)
    cmdline_file = TMPDIR / "cmdline"
    write_str_to(cmdline_file, cmdline)
    create_efi_executable(
        Path(config["DEFAULT"]["EFI_STUB"]),
        cmdline_file,
        vmlinuz,
        initramfs,
        tmp_efi_file)
    sign(KEY_DIR, tmp_efi_file, tmp_efi_file)
