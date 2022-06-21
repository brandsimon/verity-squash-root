import os
import shutil
from verify_squash_root.exec import exec_binary


class TmpfsMount():
    _directory: str

    def __init__(self, directory: str):
        self._directory = directory

    def __enter__(self):
        tmp_mount = ["mount", "-t", "tmpfs", "-o",
                     "mode=0700,uid=0,gid=0", "tmpfs", self._directory]
        os.mkdir(self._directory)
        exec_binary(tmp_mount)

    def __exit__(self, exc_type, exc_value, exc_tb):
        tmp_umount = ["umount", "-f", "-R", self._directory]
        exec_binary(tmp_umount)
        shutil.rmtree(self._directory)
