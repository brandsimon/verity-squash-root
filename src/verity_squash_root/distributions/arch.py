import os
from functools import lru_cache
from pathlib import Path
from typing import List
from verity_squash_root.file_op import read_text_from
from verity_squash_root.distributions.base import DistributionConfig


class ArchLinuxConfig(DistributionConfig):

    def efi_dirname(self) -> str:
        return "arch"

    @lru_cache(maxsize=128)
    def kernel_to_name(self, kernel: str) -> str:
        pkgbase_file = self._modules_dir / kernel / "pkgbase"
        return read_text_from(pkgbase_file).strip()

    def vmlinuz(self, kernel: str) -> Path:
        return self._modules_dir / kernel / "vmlinuz"

    def display_name(self):
        return "Arch"

    def list_kernels(self) -> List[str]:
        return os.listdir(self._modules_dir)

    def microcode_paths(self) -> List[Path]:
        return [Path("/boot/amd-ucode.img"),
                Path("/boot/intel-ucode.img")]
