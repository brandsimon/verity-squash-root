#!/usr/bin/python3
import os
import shutil
from collections.abc import Mapping
import secure_squash_root.efi as efi
import secure_squash_root.parsing as parsing
from secure_squash_root.config import TMPDIR, KERNEL_PARAM_BASE
from secure_squash_root.exec import exec_binary
from secure_squash_root.file_op import \
    read_text_from, write_str_to, merge_files


DEFAULT_CONFIG = {
    "CMDLINE": "root=UUID=a6a7b817-0979-46f2-a6f7-dfa191f9fea4 rw",
    "EFI_STUB": "/usr/lib/systemd/boot/efi/linuxx64.efi.stub",
    "SECURE_BOOT_KEYS": "/root/securebootkeys",
    "EXCLUDE_DIRS": "/home,/opt,/srv,/var/!(lib)",
    "EFI_PARTITION": "/boot/efi",
    "ROOT_MOUNT": "/mnt/root",
}


class Config:

    def __init__(self, config):
        self.__config = config

    def get(self, key):
        val = self.__config.get(key)
        if val is None:
            val = DEFAULT_CONFIG.get(key)
        return val


def str_to_exclude_dirs(s: str) -> [str]:
    return [i.strip() for i in s.split(",")]


def build_mksquashfs_cmd(exclude_dirs: [str], image: str,
                         root_mount: str, efi_partition) -> str:
    include_dirs = ["/"]
    include_empty_dirs = ["dev", "proc", "run", "sys", "tmp", root_mount,
                          efi_partition] + exclude_dirs
    options = ["-reproducible", "-xattrs", "-wildcards", "-noappend",
               "-p", "{} d 0700 0 0".format(root_mount),
               "-p", "{} d 0700 0 0".format(efi_partition)]
    cmd = ["mksquashfs"] + include_dirs + [image] + options + ["-e"]
    for d in include_empty_dirs:
        sd = d.strip("/")
        cmd += ["{}/*".format(sd)]
        cmd += ["{}/.*".format(sd)]
    return cmd


def build_veritysetup_cmd(image: str) -> str:
    return ["veritysetup", "format", image, "{}.verity".format(image)]


def veritysetup_image(image: str) -> str:
    cmd = build_veritysetup_cmd(image)
    result = exec_binary(cmd)
    stdout = result[0].decode()
    info = parsing.info_to_dict(stdout)
    return info["Root hash"]


def build_and_sign_kernel(config: Config, vmlinuz: str, initramfs: str,
                          slot: str, root_hash: str,
                          out: str, add_cmdline: str = "") -> None:
    cmdline = "{} {} {p}_slot={} {p}_hash={}".format(
        config.get("CMDLINE"),
        add_cmdline,
        slot,
        root_hash,
        p=KERNEL_PARAM_BASE)
    cmdline_file = os.path.join(TMPDIR, "cmdline")
    # Store files to sign on trusted tmpfs
    write_str_to(cmdline_file, cmdline)
    tmp_efi_file = os.path.join(TMPDIR, "tmp.efi")
    efi.create_efi_executable(
        config.get("EFI_STUB"),
        cmdline_file,
        vmlinuz,
        initramfs,
        tmp_efi_file)
    key_dir = config.get("SECURE_BOOT_KEYS")
    efi.sign(key_dir, tmp_efi_file, tmp_efi_file)
    if os.path.exists(out):
        if efi.file_matches_slot(out, slot):
            # if backup slot is booted, dont override it
            os.unlink(out)
        else:
            os.rename(out, "{}.bak".format(out))
    shutil.move(tmp_efi_file, out)


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


def merge_initram_images(main_image: str, microcode_paths: [str], out: str):
    initramfs_files = []
    for i in microcode_paths:
        if os.path.exists(i):
            merge_files.append(i)
    # main image needs to be last!
    initramfs_files.append(main_image)
    merge_files(initramfs_files, out)


class ArchLinuxConfig(DistributionConfig):
    _microcode_paths: [str] = ["/boot/intel-ucode.img", "/boot/amd-ucode.img"]
    _preset_map: Mapping[str, str] = {"default": ""}

    def file_name(self, kernel: str, preset: str) -> str:
        preset_name = self._preset_map.get(preset, preset)
        kernel_name = self._kernel_to_name(kernel)
        if preset_name == "":
            return kernel_name
        else:
            return "{}_{}".format(kernel_name, preset_name)

    def efi_dirname(self) -> str:
        return "Arch"

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
        exec_binary(["mkinitcpio", "-p", preset_path, "-A", KERNEL_PARAM_BASE])

        merged_initramfs = "{}.image".format(base_path)
        merge_initram_images(initcpio_image, self._microcode_paths,
                             merged_initramfs)
        return merged_initramfs

    def list_kernel(self) -> [str]:
        return os.listdir(self._modules_dir)

    def list_kernel_presets(self, kernel: str) -> [str]:
        name = self._kernel_to_name(kernel)
        run = "/usr/lib/secure-squash-root/mkinitcpio_list_presets"
        presets_str = exec_binary([run, name])[0].decode()
        return presets_str.strip().split("\n")


class RunProgAndCleanup:

    def __init__(self, setup: [str], cleanup: [str]):
        self.__setup = setup
        self.__cleanup = cleanup

    def __enter__(self):
        exec_binary(self.__setup)

    def __exit__(self, exc_type, exc_value, exc_tb):
        exec_binary(self.__cleanup)


def current_slot(kernel_cmdline: str) -> str:
    params = kernel_cmdline.split(" ")
    for p in params:
        if p.startswith("{}_slot=".format(KERNEL_PARAM_BASE)):
            return p[24:].lower()
    return None


def unused_slot(kernel_cmdline: str) -> str:
    curr = current_slot(kernel_cmdline)
    try:
        next_slot = {"a": "b", "b": "a"}
        return next_slot[curr]
    except KeyError:
        return "a"


def create_image_and_sign_kernel(config: Config,
                                 distribution: DistributionConfig):
    kernel_cmdline = read_text_from("/proc/cmdline")
    use_slot = unused_slot(kernel_cmdline)
    root_mount = config.get("ROOT_MOUNT")
    image = os.path.join(root_mount, "image_{}.squashfs".format(use_slot))
    efi_partition = config.get("EFI_PARTITION")
    exclude_dirs = str_to_exclude_dirs(config.get("EXCLUDE_DIRS"))
    exec_binary(build_mksquashfs_cmd(exclude_dirs, image,
                                     root_mount, efi_partition))
    root_hash = veritysetup_image(image)
    efi_dirname = distribution.efi_dirname()
    print(root_hash)

    for kernel in distribution.list_kernel():
        vmlinuz = distribution.vmlinuz(kernel)
        for preset in distribution.list_kernel_presets(kernel):
            print(kernel, preset)
            base_name = distribution.file_name(kernel, preset)
            initramfs = distribution.build_initramfs_with_microcode(
                kernel, preset)

            out_dir = os.path.join(efi_partition, "EFI", efi_dirname)
            out = os.path.join(out_dir, "{}.efi".format(base_name))
            build_and_sign_kernel(config, vmlinuz, initramfs, use_slot,
                                  root_hash, out)
            out_tmpfs = os.path.join(out_dir, "{}_tmpfs.efi".format(base_name))
            build_and_sign_kernel(config, vmlinuz, initramfs, use_slot,
                                  root_hash, out_tmpfs,
                                  "{}_volatile".format(KERNEL_PARAM_BASE))


def main():
    config = Config({})
    distribution = ArchLinuxConfig()
    os.umask(0o077)

    tmp_mount = ["mount", "-t", "tmpfs", "-o",
                 "mode=0700,uid=0,gid=0", "tmpfs", TMPDIR]
    tmp_umount = ["umount", "-f", "-R", TMPDIR]
    exec_binary(["mkdir", "-p", TMPDIR])
    with RunProgAndCleanup(tmp_mount, tmp_umount):
        create_image_and_sign_kernel(config, distribution)


if __name__ == "__main__":
    main()
