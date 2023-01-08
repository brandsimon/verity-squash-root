import logging
import os
import tarfile
from pathlib import Path
from typing import List
from verity_squash_root.config import KEY_DIR, CONFIG_DIR
from verity_squash_root.efi import DB_CERT_FILE, DB_KEY_FILE
from verity_squash_root.exec import exec_binary

SIGNING_FILES = [DB_KEY_FILE, DB_CERT_FILE]
PUBLIC_FILES = [
    "db.auth", "db.cer", "db.esl", "db.hash",
    "kek.auth", "kek.cer", "kek.esl", "kek.hash",
    "pk.auth", "pk.cer", "pk.esl", "pk.hash"]
ALL_FILES = [DB_KEY_FILE, DB_CERT_FILE,
             "pk.key", "kek.key",
             "kek.crt", "pk.crt",
             "rm_pk.auth", "guid.txt"] + PUBLIC_FILES
PUBLIC_KEY_FILES_TAR = CONFIG_DIR / "public_keys.tar"
SIGNING_FILES_TAR = CONFIG_DIR / "keys.tar.age"
ALL_FILES_TAR = CONFIG_DIR / "all_keys.tar.age"


def create_secure_boot_keys() -> None:
    exec_binary(["/usr/lib/verity-squash-root/generate_secure_boot_keys"])


def create_tar_file(files: List[str], out: Path) -> None:
    with tarfile.open(out, "w") as t:
        for file in files:
            t.add(file)


def create_encrypted_tar_file(files: List[str], out: Path) -> None:
    cmd_arr = ["/usr/lib/verity-squash-root/create_encrypted_tar_file",
               str(out)] + files
    exec_binary(cmd_arr)


def create_and_pack_secure_boot_keys() -> None:
    prev_cwd = Path.cwd()
    try:
        KEY_DIR.mkdir()
        os.chdir(KEY_DIR)
        logging.info("Creating secure boot keys...")
        create_secure_boot_keys()
        logging.info("Create archive with signing files")
        create_encrypted_tar_file(SIGNING_FILES, SIGNING_FILES_TAR)
        logging.info("Create archive with all keys")
        create_encrypted_tar_file(ALL_FILES, ALL_FILES_TAR)
        logging.info("Create archive with public keys")
        create_tar_file(PUBLIC_FILES, PUBLIC_KEY_FILES_TAR)
    finally:
        os.chdir(prev_cwd)


def check_if_archives_exist():
    for p in [PUBLIC_KEY_FILES_TAR, SIGNING_FILES_TAR, ALL_FILES_TAR]:
        if p.exists():
            raise ValueError("Archive {} already exists, delete it only if "
                             "you dont need it anymore".format(p))
