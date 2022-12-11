from collections.abc import Mapping
from pathlib import Path
from typing import List
from verity_squash_root.config import TMPDIR, NAME_DASH
from verity_squash_root.exec import exec_binary
from verity_squash_root.file_op import read_text_from, write_str_to
from verity_squash_root.initramfs import merge_initramfs_images
from verity_squash_root.distributions.base import DistributionConfig
from verity_squash_root.initramfs.base import InitramfsBuilder


class Mkinitcpio(InitramfsBuilder):
    _preset_map: Mapping[str, str] = {"default": ""}

    def __init__(self, distribution: DistributionConfig):
        self._distribution = distribution

    def file_name(self, kernel: str, preset: str) -> str:
        preset_name = self._preset_map.get(preset, preset)
        kernel_name = self._distribution.kernel_to_name(kernel)
        if preset_name == "":
            return kernel_name
        else:
            return "{}_{}".format(kernel_name, preset_name)

    def display_name(self, kernel: str, preset: str) -> str:
        preset_name = self._preset_map.get(preset, preset)
        kernel_name = self._distribution.kernel_to_name(
            kernel).replace("-", " ")
        if preset_name != "":
            preset_name = " ({})".format(preset_name)
        return "{} {}{}".format(
            self._distribution.display_name(),
            kernel_name.capitalize(),
            preset_name)

    def build_initramfs_with_microcode(self, kernel: str,
                                       preset: str) -> Path:
        name = self._distribution.kernel_to_name(kernel)
        config = read_text_from(
            Path("/etc/mkinitcpio.d") / "{}.preset".format(name))
        base_path = TMPDIR / "{}-{}".format(name, preset)
        initcpio_image = Path("{}.initcpio".format(base_path))
        preset_path = base_path.with_suffix(".preset")
        write_config = ("{}\n"
                        "PRESETS=('{p}')\n"
                        "{p}_image={}\n"
                        "{p}_options=\"${{{p}_options}} -A {}\"\n").format(
            config,
            initcpio_image,
            NAME_DASH,
            p=preset)
        write_str_to(preset_path, write_config)
        exec_binary(["mkinitcpio", "-p", str(preset_path)])

        merged_initramfs = base_path.with_suffix(".image")
        merge_initramfs_images(initcpio_image,
                               self._distribution.microcode_paths(),
                               merged_initramfs)
        return merged_initramfs

    def list_kernel_presets(self, kernel: str) -> List[str]:
        name = self._distribution.kernel_to_name(kernel)
        run = "/usr/lib/verity-squash-root/mkinitcpio_list_presets"
        presets_str = exec_binary([run, name])[0].decode()
        return presets_str.strip().split("\n")
