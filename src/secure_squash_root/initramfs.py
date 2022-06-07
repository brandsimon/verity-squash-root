import os
from typing import List
from secure_squash_root.file_op import merge_files


def merge_initramfs_images(main_image: str, microcode_paths: List[str],
                           out: str) -> None:
    initramfs_files = []
    for i in microcode_paths:
        if os.path.exists(i):
            initramfs_files.append(i)
    # main image needs to be last!
    initramfs_files.append(main_image)
    merge_files(initramfs_files, out)
