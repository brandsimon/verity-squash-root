# verity-squash-root
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
   Cmdline parameters to decrypt still need to be configured.
 - Depending on the kernel cmdline, either the A or B image will be verified
   via dm-verity and used. (The build command will set these automatically.)
   If you boot a tmpfs image, a tmpfs will be used as overlay image for
   volatile changes.
   If you boot a non-tmpfs image, the folder overlay on the root-partition
   will be used as overlayfs upper directory to save persistent changes.

## Install

 - Install verity-squash-root from [AUR](https://aur.archlinux.org/packages/verity-squash-root/)
   or install a [package built by CI](https://github.com/brandsimon/verity-squash-root-packages).
 - Create your encrypted secure-boot keys:
```bash
verity-squash-root --ignore-warnings create-keys
```
 - Mount your EFI partition and [configure](#configuration) it.
 - Add your EFI partition to `/etc/fstab`.
 - Make sure your EFI parition is big enough (1 GB recommended).
 - Create directory `/mnt/root`.
 - Mount your root-partition to `/mnt/root` and configure it in fstab file.
 - Configure your kernel cmdline  (see: [Configuration](#configuration))
 - Exclude every directory not wanted in the squashfs in the config file (`EXCLUDE_DIRS`)
 - Configure a bind-mount for every excluded directory from `/mnt/root/...`
 - Configure distribution specific options (see [Configuration](#configuration))
 - Install systemd-boot, configure it and build the first image:
```
verity-squash-root --ignore-warnings setup systemd
verity-squash-root --ignore-warnings build
```
 - Now reboot into the squashfs
 - If everything works as expected, enable secure-boot with the keys
   from `/etc/verity_squash_root/public_keys.tar`.

### Updates

 - Boot into a tmpfs image.
 - Update your distribution
 - Create new squashfs image with signed efis:
```
verity-squash-root build
```

### Using custom keys

Make yourself familiar with the process of creating, installing and using
custom Secure Boot keys. See:
 - https://wiki.archlinux.org/index.php/Secure_Boot
 - https://www.rodsbooks.com/efi-bootloaders/controlling-sb.html

After you have generated your custom keys:
```bash
cd to/your/keys/direcory
tar cf keys.tar db.key db.crt
age -p -e -o keys.tar.age keys.tar
mv keys.tar.age /etc/verity_squash_root/
rm keys.tar
```
 - Remove your plaintext keys

## Configuration

The config file is located at `/etc/verity_squash_root/config.ini`.
These config options are available:

#### Section `DEFAULT`

- `CMDLINE`: configures kernel cmdline, if not configured,
fallback to `/etc/kernel/cmdline`.
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

#### Section `EXTRA_SIGN`

You can specify files to be signed when running with the `sign_extra_files`
command. The format is:
```
NAME = SOURCE_PATH => DESTINATION_PATH
```
e.g. to sign the systemd-boot efi files:
```
[EXTRA_SIGN]
systemd-boot = /usr/lib/systemd/boot/efi/systemd-bootx64.efi => /boot/efi/EFI/systemd/systemd-bootx64.efi
```

Be careful to not specify files from untrusted sources, e.g. the ESP
partition. An attacker could exchange these files.

### Supported setups

Currently Arch Linux and Debian are supported with mkinitcpio and dracut.
Mkinitcpio is only supported, if it is used wih systemd-hooks.

## Considerations / Recommendations

 - Directly before updating, reboot into a tmpfs overlay, so modifications made
by an attacker are removed and you have your trusted environment from the last
update.
 - If you enable automatic decryption of your secure-boot keys, an
attacker who gets access can also sign efi binaries. So manually decrypting
secure-boot keys via age is more secure.
 - To be sure to only enter the password for your secure-boot keys
on your machine, you can verify your machine on boot with
[tpm2-totp](https://github.com/tpm2-software/tpm2-totp) or
[cryptographic-id](https://gitlab.com/cryptographic_id/cryptographic-id-rs).
 - Encrypt your root partition! If your encryption was handled by the
initramfs (dracut/mkinitcpio) before installation, it will work with the
squashfs root image as well.

## Usage

To list all efi images, which will be created or ignored via
`IGNORE_KERNEL_EFIS`:
```
verity-squash-root list
```

To install systemd-boot and create a UEFI Boot Manger entry for it:
```
verity-squash-root setup systemd
```

To add efi files to the UEFI Boot Manager with /dev/sda1 as EFI partition:
```
verity-squash-root setup uefi /dev/sda 1
```

To build a new squashfs image and efi files:
```
verity-squash-root build
```

If you are not yet booted in a verified image, you need `--ignore-warnings`,
since there will be a warning if the root image is not fully verified.

## Files

The following files will be used on your root-partition:

Images with verity info:

- `image_a.squashfs`, `image_a.squashfs.verity`,
- `image_b.squashfs` `image_b.squashfs.verity`

Overlayfs directories:

- `overlay` `workdir`

## Development

### Dependencies

```
age (only when used for decryption of secure-boot keys)
binutils
cryptsetup-bin
efitools
python
sbsigntool
squashfs-tools
systemd-boot-efi (only when no other efi-stub is configured)
tar
```

#### Development

```
python-pyflakes
python-pycodestyle
```

### Setup

Setup a python3 virtual environment:

```shell
git clone git@github.com:brandsimon/verity-squash-root.git
python3 -m venv .venv
.venv/bin/pip install -e . --no-deps
```

Run unit tests:

```shell
sudo mkdir -p /etc/mkinitcpio.d  # Otherwise mkinitcpio test will fail
.venv/bin/python -m unittest tests/unit/tests.py
```

## Related resources

* https://wiki.archlinux.org/index.php/Unified_Extensible_Firmware_Interface
* https://wiki.archlinux.org/index.php/Secure_Boot
* https://www.rodsbooks.com/efi-bootloaders/index.html
* https://bentley.link/secureboot/
* [sbupdate](https://github.com/andreyv/sbupdate) — tool to automatically sign
Arch Linux kernels
* [Foxboron/sbctl](https://github.com/Foxboron/sbctl) — Secure Boot Manager
