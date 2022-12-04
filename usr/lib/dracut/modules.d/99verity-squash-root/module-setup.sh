#!/bin/bash

date_or_override() {
	# allow override for reproducible builds
	if [ "${DATE_OVERRIDE}" != "" ]; then
		printf "%s\\n" "${DATE_OVERRIDE}"
	else
		date "+%Y-%m-%d %H:%M:%S %Z"
	fi
}

check() {
	return 255
}

cmdline() {
	echo "verity_squash_root_slot"
	echo "verity_squash_root_hash"
	echo "verity_squash_root_volatile"
}

depends() {
	echo "dracut-systemd"
	echo "systemd-initrd"
	return 0
}

installkernel() {
	hostonly="" instmods dm_mod dm_verity loop overlay squashfs
}

install() {
	# shellcheck disable=SC2154
	date_or_override > "${initdir}/VERIFY_SQUASH_ROOT_DATE"
	# create mount points
	mkdir -p "${initdir}"/moved_root
	mkdir -p "${initdir}"/overlayroot
	mkdir -p "${initdir}"/verify-squashfs-tmp/squashroot
	mkdir -p "${initdir}"/verify-squashfs-tmp/tmpfs
	# mount handler
	# shellcheck disable=SC2154
	inst "${moddir}/verity_squash_root.conf" \
		"${systemdsystemunitdir}/dracut-mount.service.d/"
	inst /usr/lib/verity-squash-root/mount_handler
	inst /usr/lib/verity-squash-root/mount_handler_dracut
	DRACUT_RESOLVE_DEPS=1 inst_multiple mount umount uname veritysetup
}
