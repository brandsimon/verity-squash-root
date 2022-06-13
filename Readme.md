# secure-squash-root
## Build a signed efi binary which mounts a verified squashfs image as root

### [Install](#install) - [Configuration](#configuration) - [Usage](#usage) - [Development](#development)

This library provides an easy way to create a signed efi binary which mounts a
verified squashfs image as root.

## Install

There are no installation packages at the moment.
You can clone the repository, see [Development](development)

### Dependencies

```
binutils
sbsigntools
squashfs-tools
tar
```

## Configuration

The rootfs needs to be mounted to `ROOT_MOUNT` config path and configured in `/etc/fstab`.
Make sure your EFI parition is big enough (500 MB recommended).

### Arch Linux

Only mkinitcpio is supported under Arch Linux.
Add the hook `secure-squash-root` to `/etc/mkinitcpio.conf` directly after the autodetect hook.
This is necessary, since the autodetect hook cannot handle overlayfs as rootfs (yet).

## Usage

Under construction.

## Development

Setup a python3 virtual environment:

```shell
git clone git@github.com:brandsimon/secure-squash-root.git
python3 -m venv .venv
.venv/bin/pip install -e . --no-deps
```

Run unit tests:

```shell
.venv/bin/python -m unittest tests/unit/tests.py
```
