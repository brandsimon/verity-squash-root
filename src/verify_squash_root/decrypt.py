import re
import shutil
import tarfile
from configparser import ConfigParser
from pathlib import Path
from typing import List
from verify_squash_root.config import KEY_DIR
from verify_squash_root.exec import exec_binary

TAR_FILE = KEY_DIR / "keys.tar"


def format_cmd(cmd: str, file: Path) -> List[str]:
    parts = re.split(" |\n", cmd.strip())
    return list(map(lambda x: x.format(file), parts))


def decrypt_secure_boot_keys(config: ConfigParser) -> None:
    cmd = config["DEFAULT"]["DECRYPT_SECURE_BOOT_KEYS_CMD"]
    cmd_arr = format_cmd(cmd, TAR_FILE)
    KEY_DIR.mkdir()
    exec_binary(cmd_arr)
    with tarfile.open(TAR_FILE) as t:
        
        import os
        
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(t, KEY_DIR)


class DecryptKeys:
    _config: ConfigParser

    def __init__(self, config: ConfigParser):
        self._config = config

    def __enter__(self):
        decrypt_secure_boot_keys(self._config)

    def __exit__(self, exc_type, exc_value, exc_tb):
        shutil.rmtree(KEY_DIR)
