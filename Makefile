WINE = WINEPREFIX=$(PWD)/wine wine
WINEPY = $(WINE) C:\\Python26\\python.exe
RVER = `head -n1 debian/changelog | sed 's,.*(\(.*\)).*,\1,'`
REV = `bzr revno`
RESULT="build/usb-creator-r$(REV)-$(RVER).exe"

update-po:
	find -regex "./\(usbcreator\|dbus\|gui\|desktop\).*\.\(py\|glade\|ui\|in\)" \
		| sed '/gtk\.ui/ s,^,[type: gettext/glade],' > po/POTFILES.in
	echo ./main.py >> po/POTFILES.in
	echo ./bin/usb-creator-gtk >> po/POTFILES.in
	echo ./bin/usb-creator-kde >> po/POTFILES.in
	python setup.py build_i18n --merge-po --po-dir po

check_external_deps:
	tools/check_external_deps

check_windows: check_external_deps
	$(WINEPY) ./tests/run-win

check: check_windows
	tests/run

build_windows: build_pylauncher translations
	cp wine/drive_c/Program\ Files/7-Zip/7z.exe build
	$(WINEPY) -OO tools/pypack/pypack --verbose --bytecompile --outputdir=build/usbcreator main.py tools/_include.py tools/dd.exe tools/syslinux.exe build/7z.exe build/translations
	$(WINEPY) -OO build/pylauncher/pack.py build/usbcreator
	mv build/application.exe $(RESULT)
	du -h $(RESULT)

build_pylauncher: clean check_external_deps
	cp -r tools/pylauncher build
	cp wine/drive_c/windows/system32/python26.dll build/pylauncher
	cp desktop/usb-creator.ico build/pylauncher/application.ico
	cd build/pylauncher; $(MAKE)

test_windows: build_windows
	$(WINE) $(RESULT)

clean:
	rm -rf build/*
	cd tools/pylauncher; $(MAKE) clean
	find tools/pypack -type f -name "*.pyo" -delete

translations: po/*.po
	# TODO evand 2009-07-28: Ideally we should build the mo files once,
	# instead of once here and once in setup.py.
	# Taken from Wubi.
	rm -rf build/translations
	mkdir -p build/translations/
	@for po in $^; do \
		language=`basename $$po`; \
		language=$${language%%.po}; \
		target="build/translations/$$language/LC_MESSAGES"; \
		mkdir -p $$target; \
		msgfmt --output=$$target/usbcreator.mo $$po; \
	done
