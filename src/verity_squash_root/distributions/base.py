import re
from pathlib import Path
from typing import List, MutableMapping


class DistributionConfig:

    _modules_dir: Path = Path("/usr/lib/modules")
    __os_id: str = ""
    __os_name: str = ""

    def __init__(self, os_id: str, os_name: str):
        self.__os_id = os_id
        self.__os_name = os_name

    def kernel_to_name(self, kernel: str) -> str:
        raise NotImplementedError("Base class")

    def display_name(self) -> str:
        return self.__os_name

    def efi_dirname(self) -> str:
        return self.__os_id

    def vmlinuz(self, kernel: str) -> Path:
        return self._modules_dir / kernel / "vmlinuz"

    def list_kernels(self) -> List[str]:
        def int_or_str(e):
            try:
                return int(e)
            except ValueError:
                return e

        def human_sort(e):
            return [int_or_str(a)
                    for a in re.split('([0-9]+)', e)]

        return sorted([k.name for k in self._modules_dir.iterdir()],
                      reverse=True, key=human_sort)

    def microcode_paths(self) -> List[Path]:
        raise NotImplementedError("Base class")


def calc_kernel_packages_not_unique(distribution: DistributionConfig) \
        -> List[str]:
    mapping: MutableMapping[str, str] = {}
    result = []
    for kernel in distribution.list_kernels():
        file_name = distribution.kernel_to_name(kernel)
        if file_name in mapping:
            result.append("Package {} has multiple kernel versions: {}, {}"
                          .format(file_name, kernel, mapping[file_name]))
        mapping[file_name] = kernel
    if len(result) > 0:
        result.append("This means, that there are probably old files in "
                      "/usr/lib/modules")
    return result
