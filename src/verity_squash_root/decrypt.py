import re
import shutil
import tarfile
from configparser import ConfigParser
from pathlib import Path
from typing import List
from verity_squash_root.config import KEY_DIR
from verity_squash_root.exec import exec_binary
from verity_squash_root.efi import DB_CERT_FILE, DB_KEY_FILE
TAR_FILE = KEY_DIR / "keys.tar"


def format_cmd(cmd: str, file: Path) -> List[str]:
    # split at ' ' or new line into parameters for exec
    parts = re.split(" |\n|\t", cmd.strip())
    return list(map(lambda x: x.format(file), parts))


def decrypt_secure_boot_keys(config: ConfigParser) -> None:
    cmd = config["DEFAULT"]["DECRYPT_SECURE_BOOT_KEYS_CMD"]
    cmd_arr = format_cmd(cmd, TAR_FILE)
    KEY_DIR.mkdir()
    exec_binary(cmd_arr)
    with tarfile.open(TAR_FILE) as t:
        # Only extract needed files to avoid python extract/extractall
        # vulnerability
        t.extract(DB_CERT_FILE, KEY_DIR, filter='data')
        t.extract(DB_KEY_FILE, KEY_DIR, filter='data')


class DecryptKeys:
    _config: ConfigParser

    def __init__(self, config: ConfigParser):
        self._config = config

    def __enter__(self):
        decrypt_secure_boot_keys(self._config)

    def __exit__(self, exc_type, exc_value, exc_tb):
        shutil.rmtree(KEY_DIR)
