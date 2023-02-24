import shutil
from verity_squash_root.distributions.base import DistributionConfig
from verity_squash_root.initramfs.dracut import InitramfsBuilder, \
    Dracut
from verity_squash_root.initramfs.mkinitcpio import Mkinitcpio


def autodetect_initramfs(distri: DistributionConfig) -> InitramfsBuilder:
    if shutil.which("mkinitcpio") is not None:
        return Mkinitcpio(distri)
    elif shutil.which("dracut") is not None:
        return Dracut(distri)
    else:
        raise ValueError("No supported initramfs builder found")
