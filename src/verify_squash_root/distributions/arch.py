import os
from collections.abc import Mapping
from functools import lru_cache
from typing import List
from verify_squash_root.config import TMPDIR
from verify_squash_root.exec import exec_binary
from verify_squash_root.file_op import read_text_from, write_str_to
from verify_squash_root.initramfs import merge_initramfs_images
from verify_squash_root.distributions.base import DistributionConfig


class ArchLinuxConfig(DistributionConfig):
    _microcode_paths: List[str] = [
        "/boot/intel-ucode.img", "/boot/amd-ucode.img"]
    _preset_map: Mapping[str, str] = {"default": ""}

    def file_name(self, kernel: str, preset: str) -> str:
        preset_name = self._preset_map.get(preset, preset)
        kernel_name = self._kernel_to_name(kernel)
        if preset_name == "":
            return kernel_name
        else:
            return "{}_{}".format(kernel_name, preset_name)

    def display_name(self, kernel: str, preset: str) -> str:
        preset_name = self._preset_map.get(preset, preset)
        kernel_name = self._kernel_to_name(kernel).replace("-", " ")
        if preset_name != "":
            preset_name = " ({})".format(preset_name)
        return "Arch {}{}".format(kernel_name.capitalize(), preset_name)

    def efi_dirname(self) -> str:
        return "Arch"

    @lru_cache(maxsize=128)
    def _kernel_to_name(self, kernel: str) -> str:
        pkgbase_file = os.path.join(self._modules_dir, kernel, "pkgbase")
        return read_text_from(pkgbase_file).strip()

    def vmlinuz(self, kernel: str) -> str:
        return os.path.join(self._modules_dir, kernel, "vmlinuz")

    def build_initramfs_with_microcode(self, kernel: str,
                                       preset: str) -> str:
        name = self._kernel_to_name(kernel)
        config = read_text_from(os.path.join(
            "/etc/mkinitcpio.d", "{}.preset".format(name)))
        base_path = os.path.join(TMPDIR, "{}-{}".format(
            name, preset))
        initcpio_image = "{}.initcpio".format(base_path)
        preset_path = "{}.preset".format(base_path)
        write_config = "{}\nPRESETS=('{p}')\n{p}_image={}\n".format(
            config,
            initcpio_image,
            p=preset)
        write_str_to(preset_path, write_config)
        exec_binary(["mkinitcpio", "-p", preset_path])

        merged_initramfs = "{}.image".format(base_path)
        merge_initramfs_images(initcpio_image, self._microcode_paths,
                               merged_initramfs)
        return merged_initramfs

    def list_kernels(self) -> List[str]:
        return os.listdir(self._modules_dir)

    def list_kernel_presets(self, kernel: str) -> List[str]:
        name = self._kernel_to_name(kernel)
        run = "/usr/lib/verify-squash-root/mkinitcpio_list_presets"
        presets_str = exec_binary([run, name])[0].decode()
        return presets_str.strip().split("\n")
