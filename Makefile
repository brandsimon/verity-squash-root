BASHCOMPDIR := usr/share/bash-completion/completions
DRACUTDIR := usr/lib/dracut/modules.d/99verity-squash-root
INITCPIODIR := usr/lib/initcpio/install
SERVICEDIR := usr/lib/systemd/system

.PHONY: all install

all: dist/*.whl

dist/*.whl:
	python -m build --wheel --no-isolation

install-no-py:
	install -dm 755 $(DESTDIR)
	install -dm 755 $(DESTDIR)/usr/lib/verity-squash-root
	install -dm 755 $(DESTDIR)/$(INITCPIODIR)
	install -dm 755 $(DESTDIR)/$(BASHCOMPDIR)
	install -dm 755 $(DESTDIR)/usr/share/licenses/verity-squash-root
	install -dm 755 $(DESTDIR)/usr/share/verity_squash_root/ \
		$(DESTDIR)/etc/verity_squash_root/
	install -Dm 644 src/verity_squash_root/default_config.ini \
		$(DESTDIR)/usr/share/verity_squash_root/default.ini
	install -Dm 600 src/verity_squash_root/default_config.ini \
		$(DESTDIR)/etc/verity_squash_root/config.ini
	install -Dm 755 usr/lib/verity-squash-root/* \
		$(DESTDIR)/usr/lib/verity-squash-root
	install -dm 755 $(DESTDIR)/$(DRACUTDIR)
	install -Dm 755 $(DRACUTDIR)/module-setup.sh \
		$(DESTDIR)/$(DRACUTDIR)
	install -Dm 644 $(DRACUTDIR)/cryptsetup_overlay.conf \
		$(DESTDIR)/$(DRACUTDIR)
	install -Dm 644 $(DRACUTDIR)/dracut_mount_overlay.conf \
		$(DESTDIR)/$(DRACUTDIR)
	install -Dm 644 $(INITCPIODIR)/verity-squash-root \
		$(DESTDIR)/$(INITCPIODIR)
	install -Dm 755 $(BASHCOMPDIR)/verity-squash-root \
		$(DESTDIR)/$(BASHCOMPDIR)
	install -dm 755 $(DESTDIR)/$(SERVICEDIR)
	install -Dm 644 $(SERVICEDIR)/verity-squash-root-notify.service \
		$(DESTDIR)/$(SERVICEDIR)/verity-squash-root-notify.service
	install -Dm 644 LICENSE.txt \
		$(DESTDIR)/usr/share/licenses/verity-squash-root

install: dist/*.whl install-no-py
	python -m installer --destdir=$(DESTDIR) dist/*.whl
