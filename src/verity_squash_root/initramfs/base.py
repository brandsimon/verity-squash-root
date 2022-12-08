from pathlib import Path
from typing import Generator, List, Tuple
from verity_squash_root.distributions.base import DistributionConfig


class InitramfsBuilder:

    def file_name(self, kernel: str, preset: str) -> str:
        raise NotImplementedError("Base class")

    def display_name(self, kernel: str, preset: str) -> str:
        raise NotImplementedError("Base class")

    def build_initramfs_with_microcode(self, kernel: str,
                                       preset: str) -> Path:
        raise NotImplementedError("Base class")

    def list_kernel_presets(self, kernel: str) -> List[str]:
        raise NotImplementedError("Base class")


def iterate_distribution_efi(distribution: DistributionConfig,
                             initramfs: InitramfsBuilder) \
        -> Generator[Tuple[str, str, str], None, None]:
    for kernel in distribution.list_kernels():
        for preset in initramfs.list_kernel_presets(kernel):
            base_name = initramfs.file_name(kernel, preset)
            yield (kernel, preset, base_name)
