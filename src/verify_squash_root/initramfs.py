from pathlib import Path
from typing import List
from verify_squash_root.file_op import merge_files


def merge_initramfs_images(main_image: Path, microcode_paths: List[Path],
                           out: Path) -> None:
    initramfs_files = []
    for i in microcode_paths:
        if i.exists():
            initramfs_files.append(i)
    # main image needs to be last!
    initramfs_files.append(main_image)
    merge_files(initramfs_files, out)
