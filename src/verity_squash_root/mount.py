import shutil
from pathlib import Path
from verity_squash_root.exec import exec_binary


class TmpfsMount():
    _directory: Path

    def __init__(self, directory: Path):
        self._directory = directory

    def __enter__(self):
        tmp_mount = ["mount", "-t", "tmpfs", "-o",
                     "mode=0700,uid=0,gid=0", "tmpfs", str(self._directory)]
        self._directory.mkdir()
        exec_binary(tmp_mount)

    def __exit__(self, exc_type, exc_value, exc_tb):
        tmp_umount = ["umount", "-f", "-R", str(self._directory)]
        exec_binary(tmp_umount)
        shutil.rmtree(self._directory)
