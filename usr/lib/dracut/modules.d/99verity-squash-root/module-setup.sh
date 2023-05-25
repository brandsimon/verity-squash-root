#!/bin/bash

date_or_override() {
	# allow override for reproducible builds
	if [ "${DATE_OVERRIDE}" != "" ]; then
		printf "%s\\n" "${DATE_OVERRIDE}"
	else
		date "+%Y-%m-%d %H:%M:%S %Z"
	fi
}

warn_security() {
	# shellcheck disable=SC2154
	if [ "${hostonly}" = "" ]; then
		dwarning ""
		dwarning "##################################################"
		dwarning "verity-squash-root: not using hostonly will allow"
		dwarning "                    login to the emergency console"
		dwarning "##################################################"
		dwarning ""
	fi
}

check() {
	warn_security
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
	# install all filesystems, since on debian the lower fs is
	# not detected
	hostonly="" instmods "=fs"
}

install() {
	warn_security
	# shellcheck disable=SC2154
	date_or_override > "${initdir}/VERITY_SQUASH_ROOT_DATE"
	# create mount points
	mkdir -p "${initdir}"/moved_root
	mkdir -p "${initdir}"/overlayroot
	mkdir -p "${initdir}"/verity-squash-root-tmp/squashroot
	mkdir -p "${initdir}"/verity-squash-root-tmp/tmpfs
	# shellcheck disable=SC2154
	local ssud="${systemdsystemunitdir}"
	# shellcheck disable=SC2154
	local mod="${moddir}"
	inst "${mod}/dracut_mount_overlay.conf" \
		"${ssud}/dracut-mount.service.d/verity-squash-root.conf"
	inst "${mod}/cryptsetup_overlay.conf" \
		"${ssud}/systemd-cryptsetup@.service.d/verity-squash-root.conf"
	inst /usr/lib/systemd/system/verity-squash-root-notifiy.service

	inst /usr/lib/verity-squash-root/functions
	inst /usr/lib/verity-squash-root/mount_handler
	inst /usr/lib/verity-squash-root/mount_handler_dracut
	inst /usr/lib/verity-squash-root/show_boot_info
	DRACUT_RESOLVE_DEPS=1 inst_multiple mount umount sed sleep veritysetup

	# needed for veritysetup
	inst_binary dmeventd
	inst_binary dmsetup
	inst_rules 55-dm.rules
	inst_rules 95-dm-notify.rules
}
