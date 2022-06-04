class DistributionConfig:

    _modules_dir: str = "/usr/lib/modules"

    def file_name(self, kernel: str, preset: str) -> str:
        raise NotImplementedError("Base class")

    def efi_dirname(self) -> str:
        raise NotImplementedError("Base class")

    def vmlinuz(self, kernel: str) -> str:
        raise NotImplementedError("Base class")

    def build_initramfs_with_microcode(self, kernel: str,
                                       preset: str) -> str:
        raise NotImplementedError("Base class")

    def list_kernel(self) -> [str]:
        raise NotImplementedError("Base class")

    def list_kernel_presets(self, kernel: str) -> [str]:
        raise NotImplementedError("Base class")
