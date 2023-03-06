from pathlib import Path
from verity_squash_root.distributions.base import DistributionConfig


class DebianConfig(DistributionConfig):

    def kernel_to_name(self, kernel: str) -> str:
        kernels = self.list_kernels()
        pos = kernels.index(kernel)
        if pos == 0:
            return "current"
        elif pos == 1:
            return "old"
        else:
            return "old_x{}".format(pos)

    def vmlinuz(self, kernel: str) -> Path:
        return Path("/boot") / "vmlinuz-{}".format(kernel)
