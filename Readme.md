# verify-squash-root
## Build signed efi binaries which mount a dm-verity verified squashfs image as rootfs on boot.

### [Install](#install) - [Configuration](#configuration) - [Usage](#usage) - [Development](#development)

This repository provides an easy way to create signed efi binaries which mount a
verified squashfs (dm-verity) image as rootfs on boot (in the initramfs/initrd).
Also it creates A/B-style image and efi files. The current booted image will not
be overriden, so you can boot an old known-working image if there are problems.
The A/B images are stored on the configured root-partition, so they will still
be encrypted, if encryption of the root image is configured.

#### What happens on boot?

 - The initramfs mounts the root-partition as before.
   This is why encryption of the root-partition still works.
   Cmdline parameters to decrypt still need to be configured in the config file
   as `CMDLINE`.
 - Depending on the kernel cmdline, either the A or B image will be verified
   via dm-verity and used. (The build command will set these automatically.)
   If you boot a tmpfs image, a tmpfs will be used as overlay image for
   volatile changes.
   If you boot a non-tmpfs image, the folder overlay on the root-partition
   will be used as overlayfs upper directory to save persistent changes.

## Install

There are no installation packages at the moment.
You can clone the repository, see [Development](development)

### Dependencies

```
age (only when used for decryption of secure-boot keys)
binutils
python
sbsigntools
squashfs-tools
tar
```

## Configuration

The rootfs needs to be mounted to `ROOT_MOUNT` config path and configured in `/etc/fstab`.
Make sure your EFI parition is big enough (500 MB recommended).

- `CMDLINE`: configures additional kernel cmdline.
- `EFI_STUB`: path to efi stub, default is the one provided by systemd.
- `DECRYPT_SECURE_BOOT_KEYS_CMD`: Command to decrypt your secure-boot keys
tarfile, {} will be replaced with the output tar file. `db.key` and `db.crt`
in the tarfile are used to sign the efi binaries.
- `EXCLUDE_DIRS`: These directories are not included in the squashfs image.
`EFI_PARTITION` and `ROOT_MOUNT` are excluded automatically.
- `EFI_PARTITION`: Path to your efi partition. Efi binaries and systemd-boot
configuration files are stored there.
- `ROOT_MOUNT`: Path to your "original" root partition.
- `IGNORE_KERNEL_EFIS`: Which efi binaries are not built. You can use the
`list` parameter to show which can exist and which are excluded already.

### Arch Linux

Only mkinitcpio wih systemd-hooks is supported under Arch Linux.
Add the hook `verify-squash-root` to `/etc/mkinitcpio.conf` directly after the autodetect hook.
This is necessary, since the autodetect hook cannot handle overlayfs as rootfs (yet).

### Considerations / Recommendations

 - Directly before updating, reboot into a tmpfs overlay, so modifications by
an attacker are removed and you have your trusted environment from the last
update.
 - If you enable automatic decryption of your secure-boot keys, an
attacker who got access can also sign efi binaries.
 - To be sure to only enter the password for your secure-boot keys
on your machine, you can verify your machine with OTP keys on boot.
 - Encrypt your root partition! If your encryption was handled by the
initramfs before installation, it will work with the squashfs root
image as well.

## Usage

To list all efi images, which will be created or ignored via
`IGNORE_KERNEL_EFIS`:
```
verify-squash-root list
```

To install systemd-boot and create a UEFI Boot Manger entry for it:
```
verify-squash-root setup systemd
```

To add efi files to the UEFI Boot Manager with /dev/sda1 as EFI partition:
```
verify-squash-root setup uefi /dev/sda 1
```

To build a new squashfs image and efi files:
```
verify-squash-root build
```

If you are not yet booted in a verified image, you need `--ignore-warnings`,
since there will be a warning if the root image is not fully verified.

## Files

The following files will be used on your root-partition:

Images with verity info:

`image_a.squashfs`, `image_a.squashfs.verity`,
`image_b.squashfs` `image_b.squashfs.verity~

Overlayfs directories:

`overlay` `workdir`

## Development

Setup a python3 virtual environment:

```shell
git clone git@github.com:brandsimon/verify-squash-root.git
python3 -m venv .venv
.venv/bin/pip install -e . --no-deps
```

Run unit tests:

```shell
.venv/bin/python -m unittest tests/unit/tests.py
```
