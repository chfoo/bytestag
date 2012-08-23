DESTDIR=out/

build: build-doc build-py

install: install-doc install-py

clean: clean-doc clean-py
	rm -rvf out/

build-doc:
	mkdir -p doc/apiautogen/
	echo "This directory and its files were generated automatically. Do not edit!" \
		> doc/apiautogen/README
	sphinx-apidoc src/py3/bytestag -o doc/apiautogen/ -f
	make -C doc/ html

install-doc: build-doc
	mkdir -pv $(DESTDIR)/share/doc/bytestag/
	cp -rv doc/_build/html $(DESTDIR)/share/doc/bytestag/

clean-doc:
	make -C doc/ clean
	rm -rvf doc/apiautogen/

build-py:
	./setup.py build

install-py: build-py
	./setup.py install --prefix $(DESTDIR)
	
clean-py:
	./setup.py clean
	rm -rvf build/
	rm -rvf dist/
