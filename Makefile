build: build-doc build-py build-app build-daemon

install: install-doc install-py install-app install-daemon

clean: clean-doc clean-py clean-app clean-daemon
	find src/py3/ -type d -name '__pycache__' -exec rm -r {} +

build-doc:
	mkdir -p doc/apiautogen/
	echo "This directory and its files were generated automatically. Do not edit!" \
		> doc/apiautogen/README
	sphinx-apidoc src/py3/bytestag -o doc/apiautogen/ -f
	make -C doc/ html

install-doc: build-doc
	mkdir -pv $(DESTDIR)/usr/share/doc/pybytestag/
	cp -rv doc/_build/html $(DESTDIR)/usr/share/doc/pybytestag/

clean-doc:
	make -C doc/ clean
	rm -rvf doc/apiautogen/

build-py:
	./setup.py build

install-py: build-py
	./setup.py install --prefix $(DESTDIR)/usr/
	
clean-py:
	./setup.py clean
	rm -rvf build/
	rm -rvf dist/

build-app:
	mkdir -pv build/share/bytestag/bytestagui/
	rsync --verbose --recursive --times \
		--exclude '*~' --exclude '__pycache__' --exclude '~.pyc' \
		src/py3/bytestagui build/share/bytestag/
		
	mkdir -pv build/pixmaps/
	
	cp -v img/logo/hicolor/16x16/apps/bytestag_app.png \
		build/pixmaps/bytestag_app_16.png
	convert build/pixmaps/bytestag_app_16.png \
		build/pixmaps/bytestag_app_16.xpm
	
	cp -v img/logo/hicolor/32x32/apps/bytestag_app.png \
		build/pixmaps/bytestag_app_32.png
	convert build/pixmaps/bytestag_app_16.png \
		build/pixmaps/bytestag_app_32.xpm
		
	mkdir -pv build/icons/
	cp -rv img/logo/hicolor build/icons/
	
install-app: build-app
	mkdir -pv $(DESTDIR)/usr/share/bytestag/
	cp -rv build/share/bytestag/* $(DESTDIR)/usr/share/bytestag/
	
	mkdir -pv $(DESTDIR)/usr/bin/
	cp -v pkg/bin/bytestag $(DESTDIR)/usr/bin/
	
	mkdir -pv $(DESTDIR)/usr/share/pixmaps/bytestag/
	cp -rv build/pixmaps/* $(DESTDIR)/usr/share/pixmaps/bytestag/
	
	cp -rv build/icons $(DESTDIR)/usr/share/
	
	mkdir -pv $(DESTDIR)/usr/share/applications/
	cp -v pkg/bytestag.desktop $(DESTDIR)/usr/share/applications/

clean-app:
	rm -rvf build/

build-daemon:

install-daemon: build-daemon
	mkdir -pv $(DESTDIR)/etc/
	cp -rv pkg/etc/bytestagd $(DESTDIR)/etc/
	
	mkdir -pv $(DESTDIR)/usr/sbin/
	cp -v pkg/sbin/bytestagd $(DESTDIR)/usr/sbin/
	cp -rv pkg/etc/bytestagd $(DESTDIR)/etc/

clean-daemon:

