from pathlib import Path
from typing import Generator, List, MutableMapping, Tuple


class DistributionConfig:

    _modules_dir: Path = Path("/usr/lib/modules")

    def file_name(self, kernel: str, preset: str) -> str:
        raise NotImplementedError("Base class")

    def display_name(self, kernel: str, preset: str) -> str:
        raise NotImplementedError("Base class")

    def efi_dirname(self) -> str:
        raise NotImplementedError("Base class")

    def vmlinuz(self, kernel: str) -> Path:
        raise NotImplementedError("Base class")

    def build_initramfs_with_microcode(self, kernel: str,
                                       preset: str) -> Path:
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


def calc_kernel_packages_not_unique(distribution: DistributionConfig) \
        -> List[str]:
    mapping: MutableMapping[str, str] = {}
    result = []
    for kernel in distribution.list_kernels():
        file_name = distribution.file_name(kernel, "")
        if file_name in mapping:
            result.append("Package {} has multiple kernel versions: {}, {}"
                          .format(file_name, kernel, mapping[file_name]))
        mapping[file_name] = kernel
    if len(result) > 0:
        result.append("This means, that there are probably old files in "
                      "/usr/lib/modules")
    return result
