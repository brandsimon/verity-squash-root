import logging
import os
import shutil
import secure_squash_root.efi as efi
from typing import Union


def move_kernel_to(src: str, dst: str, slot: str,
                   dst_backup: Union[str, None]) -> None:
    if os.path.exists(dst):
        slot_matches = efi.file_matches_slot(dst, slot)
        if slot_matches or dst_backup is None:
            # if backup slot is booted, dont override it
            if dst_backup is None:
                logging.debug("Backup ignored")
            elif slot_matches:
                logging.debug("Backup slot kept as is")
            os.unlink(dst)
        else:
            logging.info("Moving old efi to backup")
            logging.debug("Path: {}".format(dst_backup))
            os.rename(dst, dst_backup)
    shutil.move(src, dst)
