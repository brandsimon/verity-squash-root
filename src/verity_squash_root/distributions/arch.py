from functools import lru_cache
from pathlib import Path
from typing import List
from verity_squash_root.file_op import read_text_from
from verity_squash_root.distributions.base import DistributionConfig


class ArchLinuxConfig(DistributionConfig):

    @lru_cache(maxsize=128)
    def kernel_to_name(self, kernel: str) -> str:
        pkgbase_file = self._modules_dir / kernel / "pkgbase"
        return read_text_from(pkgbase_file).strip()

    def display_name(self) -> str:
        return "Arch"

    def microcode_paths(self) -> List[Path]:
        return [Path("/boot/amd-ucode.img"),
                Path("/boot/intel-ucode.img")]
