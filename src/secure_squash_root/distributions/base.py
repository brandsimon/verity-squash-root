from typing import Generator, List, Tuple


class DistributionConfig:

    _modules_dir: str = "/usr/lib/modules"

    def file_name(self, kernel: str, preset: str) -> str:
        raise NotImplementedError("Base class")

    def display_name(self, kernel: str, preset: str) -> str:
        raise NotImplementedError("Base class")

    def efi_dirname(self) -> str:
        raise NotImplementedError("Base class")

    def vmlinuz(self, kernel: str) -> str:
        raise NotImplementedError("Base class")

    def build_initramfs_with_microcode(self, kernel: str,
                                       preset: str) -> str:
        raise NotImplementedError("Base class")

    def list_kernels(self) -> List[str]:
        raise NotImplementedError("Base class")

    def list_kernel_presets(self, kernel: str) -> List[str]:
        raise NotImplementedError("Base class")


def iterate_distribution_efi(distribution: DistributionConfig) \
        -> Generator[Tuple[str, str, str], None, None]:
    for kernel in distribution.list_kernels():
        for preset in distribution.list_kernel_presets(kernel):
            base_name = distribution.file_name(kernel, preset)
            yield (kernel, preset, base_name)
